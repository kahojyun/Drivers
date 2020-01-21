#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import atsapi as ats
import SDK_helper as atsh
import time
import ctypes
# from scipy.interpolate import interp1d

# class Error(Exception):
#     pass



class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements the Acqiris card driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        self.signal_index = {
            'Ch1 - Data': 0,
            'Ch2 - Data': 1,
            'FFT - Data': 0}
        self.board = ats.Board(systemId = 1, boardId = 1)
        # check model
        self.setModel(self.getBoardModel())
        if self.getModel() in ('ATS9870'):
            # ATS9870 doesn't support on-board FFT
            self.setOptions([])
        memorySize_samples, bitsPerSample = self.board.getChannelInfo()
        self.bitsPerSample = bitsPerSample.value
        self.bytesPerSample = (self.bitsPerSample + 7) // 8
        self.buffers = []
        self.configure_board()

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        self.board.abortAsyncRead()

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # Mark need configuaration
        self.bConfig = True
        quant.setValue(value)
        if self.isFinalCall(options):
            # Validate all settings
            value = self.validate_settings(quant, value)
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        if quant.name in self.signal_index:
            # check if first call, if so get new traces
            if self.isFirstCall(options):
                nSample = self.getValue('Number of samples')
                nRecord = self.getValue('Number of records')
                nAverage = self.getValue('Number of averages')
                ch1 = int(self.getValue('Ch1 - Enabled'))
                ch2 = int(self.getValue('Ch2 - Enabled'))
                channelCount = ch1 + ch2
                self.lTrace = [np.zeros(nSample), np.zeros(nSample)]
                if self.bConfig:
                    self.configure_board()
                    self.plan_acquisition(nRecord, nAverage)
                    self.prepare_buffer()
                try:
                    self.arming()
                    self.acquire_data(self.get_averager(channelCount, nRecord, nAverage))
                finally:
                    self.board.abortAsyncRead()
                if ch1 and ch2:
                    rs = self.vData.reshape(-1, 2)
                    self.lTrace[0] = self.channel_range[0] * rs[:nSample, 0]
                    self.lTrace[1] = self.channel_range[1] * rs[:nSample, 1]
                elif ch1:
                    self.lTrace[0] = self.channel_range[0] * rs[:nSample]
                elif ch2:
                    self.lTrace[1] = self.channel_range[1] * rs[:nSample]
            value = quant.getTraceDict(self.lTrace[self.signal_index[quant.name]],
                                        dt=1/self.getValue('Sample rate'))
        else:
            # Unable to get configuaration from board. Return stored values.
            value = quant.getValue()
        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        pass

    def get_board_model(self):
        modelId = self.board.getBoardKind()
        try:
            name = next(filter(lambda key: getattr(ats, key) == modelId, ats.boardNames))
            return name
        except:
            raise Exception("Unknown board model")

    def validate_settings(self, quant=None, value=None):
        sample_rate = self.getValue('Sample rate')
        model = self.getModel()
        if self.getValue('Clock source') == 'Internal':
            key = atsh.choose_internal_sample_rate(model, sample_rate)
            self.setValue('Sample rate', atsh.SAMPLE_RATE_VALUE[key])
        elif self.getValue('Clock source') == '10 MHz Reference':
            sr, deci = atsh.choose_external_sample_rate(model, sample_rate)
            self.setValue('Sample rate', sr)
        if quant:
            return quant.getValue()

    # Configures a board for acquisition
    def configure_board(self):
        # TODO: Select clock parameters as required to generate this
        # sample rate
        #
        # For example: if samplesPerSec is 100e6 (100 MS/s), then you can
        # either:
        #  - select clock source INTERNAL_CLOCK and sample rate
        #    SAMPLE_RATE_100MSPS
        #  - or select clock source FAST_EXTERNAL_CLOCK, sample rate
        #    SAMPLE_RATE_USER_DEF, and connect a 100MHz signal to the
        #    EXT CLK BNC connector
        # Retry setting capture clock. Avoid 'PLL not locked' error.
        self.validate_settings()
        n = 0
        retry = 5
        model = self.getModel()
        # should be correct after validation
        sample_rate = self.getValue('Sample rate')
        while True:
            n += 1
            try:
                if self.getValue('Clock source') == 'Internal':
                    sr_id = atsh.choose_internal_sample_rate(model, sample_rate)
                    self.board.setCaptureClock(ats.INTERNAL_CLOCK,
                                        sr_id,
                                        ats.CLOCK_EDGE_RISING,
                                        0)
                else:
                    sr, deci = atsh.choose_external_sample_rate(model, sample_rate)
                    self.board.setCaptureClock(ats.EXTERNAL_CLOCK_10MHz_REF,
                                        sr,
                                        ats.CLOCK_EDGE_RISING,
                                        deci)
            except Exception as e:
                if n > retry:
                    raise e
                time.sleep(1)
                continue
            break

        for n in range(2):
            ch = n+1
            if self.getValue(f'Ch{ch} - Enable'):
                # TODO: Select input parameters as required.
                coupling = self.getCmdStringFromValue(f'Ch{ch} - Coupling')
                input_range = self.getCmdStringFromValue(f'Ch{ch} - Range')
                self.channel_range[n] = atsh.INPUT_RANGE_VALUE[input_range]
                impedance = self.getCmdStringFromValue(f'Ch{ch} - Impedance')
                self.board.inputControlEx(ats.channels[n],
                                    getattr(ats, coupling),
                                    getattr(ats, input_range),
                                    getattr(ats, impedance))
                if self.getModel() in ('ATS9870'):
                    # TODO: Select bandwidth limit as required.
                    bw_limit = int(self.getValue(f'Ch{ch} - Bandwidth limit'))
                    self.board.setBWLimit(ats.channels[n], bw_limit)
        
        # TODO: Select trigger inputs and levels as required.
        trig_source = self.getCmdStringFromValue('Trig source')
        trig_slope = self.getCmdStringFromValue('Trig slope')
        trig_level = self.getValue('Trig level')
        ext_trig_range = atsh.HARDWARE_SPEC['EXT_TRIG_RANGE'][self.getModel()]
        trig_coupling = self.getCmdStringFromValue('Trig coupling')
        if trig_source == 'TRIG_CHAN_A':
            input_range = self.getCmdStringFromValue('Ch1 - Range')
            input_range_volts = self.channel_range[0]
        elif trig_source == 'TRIG_CHAN_B':
            input_range = self.getCmdStringFromValue('Ch2 - Range')
            input_range_volts = self.channel_range[1]
        elif trig_source == 'TRIG_EXTERNAL':
            input_range_volts = atsh.EXT_TRIG_RANGE_VALUE[ext_trig_range]
        else:
            input_range_volts = 1
            trig_level = 0
        trig_level_code = int(128 + 127 * trig_level / input_range_volts)
        self.board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                ats.TRIG_ENGINE_J,
                                getattr(ats, trig_source),
                                getattr(ats, trig_slope),
                                trig_level_code,
                                ats.TRIG_ENGINE_K,
                                ats.TRIG_DISABLE,
                                ats.TRIGGER_SLOPE_POSITIVE,
                                128)

        # TODO: Select external trigger parameters as required.
        self.board.setExternalTrigger(getattr(ats, trig_coupling),
                                getattr(ats, ext_trig_range))

        # TODO: Set trigger delay as required.
        triggerDelay_sec = self.getValue('Trig delay')
        triggerDelay_samples = int(triggerDelay_sec * sample_rate + 0.5)
        self.board.setTriggerDelay(triggerDelay_samples)

        # TODO: Set trigger timeout as required.
        #
        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        if trig_source == 'TRIG_DISABLE':
            triggerTimeout_sec = self.getValue('Trig interval')
        else:
            triggerTimeout_sec = 0
        triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
        self.board.setTriggerTimeOut(triggerTimeout_clocks)

        # Configure AUX I/O connector as required
        self.board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                            0)
        self.log('Finish board configuration.')

    def plan_acquisition(self, nRecord=1, nAverage=1):
        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0

        # TODO: Select the number of samples per record.
        MIN_SIZE_RES = atsh.HARDWARE_SPEC['MIN_SIZE_RES'][self.getModel()]
        MIN_REC_SIZE = atsh.HARDWARE_SPEC['MIN_REC_SIZE'][self.getModel()]
        nSample = self.getValue('Number of samples')
        postTriggerSamples = int(np.ceil(nSample/MIN_SIZE_RES)*MIN_SIZE_RES)
        postTriggerSamples = max(postTriggerSamples, MIN_REC_SIZE)

        # TODO: Select the active channels.
        ch1 = int(self.getValue('Ch1 - Enabled'))
        ch2 = int(self.getValue('Ch2 - Enabled'))
        channelCount = ch1 + ch2

        # Compute the number of bytes per record
        bytesPerSample = self.bytesPerSample
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord

        # TODO: Select the number of records per DMA buffer.
        nTotal = nRecord*nAverage
        totalBytes = nTotal*bytesPerRecord*channelCount
        # Compute the number of bytes per buffer
        # Limit the size of a buffer
        if totalBytes < 16*1024*1024:
            bytesPerBuffer = totalBytes
        elif totalBytes > 16*16*1024*1024:
            bytesPerBuffer = 16*1024*1024
        else:
            bytesPerBuffer = np.sqrt(totalBytes/1024/1024)*1024*1024
        recordsPerBuffer = int(np.ceil(bytesPerBuffer/bytesPerRecord/channelCount))
        # TODO: Select the number of buffers per acquisition.
        buffersPerAcquisition = int(np.ceil(nTotal/recordsPerBuffer))
        
        self.samplesPerRecord = samplesPerRecord
        self.recordsPerBuffer = recordsPerBuffer
        self.buffersPerAcquisition = buffersPerAcquisition
        self.log('Finish acquisition planning.')
        self.log(f'samples: {nSample}, records: {nRecord}, average: {nAverage}')
        self.log(f'Bytes per sample: {self.bytesPerSample}')
        self.log(f'Samples per record: {self.samplesPerRecord}')
        self.log(f'Records per buffer: {self.recordsPerBuffer}')
        self.log(f'Buffers per acquisition: {self.buffersPerAcquisition}')
    
    def prepare_buffer(self):
        bytesPerRecord = self.bytesPerSample * self.samplesPerRecord
        bytesPerBuffer = bytesPerRecord * self.recordsPerBuffer

        # TODO: Select number of DMA buffers to allocate
        bufferCount = 10

        # Allocate DMA buffers
        sample_type = ctypes.c_uint8
        if self.bytesPerSample > 1:
            sample_type = ctypes.c_uint16

        self.buffers.clear()
        for i in range(bufferCount):
            self.buffers.append(ats.DMABuffer(self.board.handle, sample_type, bytesPerBuffer))
        self.log(f'Allocate {bufferCount} buffers, size: {bytesPerBuffer} bytes')

    def arming(self):
        # Set the record size. No pre-trigger samples.
        self.board.setRecordSize(0, self.samplesPerRecord)

        recordsPerAcquisition = self.recordsPerBuffer * self.buffersPerAcquisition
        channels = 0
        for i in range(2):
            if self.getValue(f'Ch{i} - Enabled'):
                channels |= ats.channels[i]

        # Configure the board to make an NPT AutoDMA acquisition
        self.board.beforeAsyncRead(channels,
                            0,
                            self.samplesPerRecord,
                            self.recordsPerBuffer,
                            recordsPerAcquisition,
                            ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT | ats.ADMA_INTERLEAVE_SAMPLES)
        
        # Post DMA buffers to board
        for buffer in self.buffers:
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        self.board.startCapture()
        self.log(f'Start capturing')

    def convert_adc_to_one(self, data):
        bitsPerSample = self.bitsPerSample
        #  Right-shift raw data to get sample code
        bitShift = (-bitsPerSample) % 8
        codeZero = (1 << (bitsPerSample - 1)) - 0.5
        codeRange = (1 << (bitsPerSample - 1)) - 0.5
        return ((data >> bitShift) - codeZero) / codeRange

    def get_averager(self, channelCount, nRecord=1, nAverage=1):
        self.vData = np.zeros(self.samplesPerRecord*nRecord*channelCount)
        self.nRecordCompleted = 0
        def averager(data, channelCount, nRecord, nAverage):
            uni_data = self.convert_adc_to_one(data)
            recPerBuf = self.recordsPerBuffer
            sPerRec = self.samplesPerRecord
            recComp = self.nRecordCompleted
            nTotal = nRecord * nAverage
            # drop extra data
            if recComp + recPerBuf > nTotal:
                recPerBuf = nTotal - recComp
                uni_data = uni_data[:sPerRec*recPerBuf*channelCount]
            pos = (recComp % nRecord)*sPerRec
            pre = len(self.vData) - pos
            if pos + len(uni_data) <= len(self.vData):
                self.vData[pos: pos+len(uni_data)] += uni_data
            else:
                self.vData[pos:] += uni_data[:pre]
                post = (len(uni_data) - pre) % len(self.vData)
                if post > 0:
                    self.vData += np.sum(uni_data[pre: -post].reshape(-1, len(self.vData)), axis=0)
                else:
                    self.vData += np.sum(uni_data[pre:].reshape(-1, len(self.vData)), axis=0)
            self.nRecordCompleted += recPerBuf
        return lambda x: averager(x, channelCount, nRecord, nAverage)
        
    def acquire_data(self, process_buffer):
        start = time.perf_counter() # Keep track of when acquisition started
        try:
            buffersCompleted = 0
            bytesTransferred = 0
            while (buffersCompleted < self.buffersPerAcquisition and not
                self.isStopped()):
                # Wait for the buffer at the head of the list of available
                # buffers to be filled by the board.
                buffer = self.buffers[buffersCompleted % len(self.buffers)]
                self.board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
                buffersCompleted += 1
                bytesTransferred += buffer.size_bytes

                # TODO: Process sample data in this buffer. Data is available
                # as a NumPy array at buffer.buffer
                process_buffer(buffer.buffer)
                progress = buffersCompleted/self.buffersPerAcquisition
                self.reportStatus(f'Acquiring traces ({progress}%)')

                # NOTE:
                #
                # While you are processing this buffer, the board is already
                # filling the next available buffer(s).
                #
                # You MUST finish processing this buffer and post it back to the
                # board before the board fills all of its available DMA buffers
                # and on-board memory.
                #
                # Samples are arranged in the buffer as follows:
                # S0A, S0B, ..., S1A, S1B, ...
                # with SXY the sample number X of channel Y.
                #
                # Sample code are stored as 8-bit values.
                #
                # Sample codes are unsigned by default. As a result:
                # - 0x00 represents a negative full scale input signal.
                # - 0x80 represents a ~0V signal.
                # - 0xFF represents a positive full scale input signal.
                # Optionaly save data to file
                # Add the buffer to the end of the list of available buffers.
                self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
        finally:
            self.board.abortAsyncRead()
        # Compute the total transfer time, and display performance information.
        transferTime_sec = time.perf_counter() - start
        self.log("Capture completed in %f sec" % transferTime_sec)
        buffersPerSec = 0
        bytesPerSec = 0
        recordsPerSec = 0
        if transferTime_sec > 0:
            buffersPerSec = buffersCompleted / transferTime_sec
            bytesPerSec = bytesTransferred / transferTime_sec
            recordsPerSec = self.recordsPerBuffer * buffersCompleted / transferTime_sec
        self.log("Captured %d buffers (%f buffers per sec)" %
            (buffersCompleted, buffersPerSec))
        self.log("Captured %d records (%f records per sec)" %
            (self.recordsPerBuffer * buffersCompleted, recordsPerSec))
        self.log("Transferred %d bytes (%f bytes per sec)" %
            (bytesTransferred, bytesPerSec))

    # def performOpen(self, options={}):
    #     """Perform the operation of opening the instrument connection"""
    #     # init object
    #     self.dig = None
    #     # keep track of sampled traces
    #     self.lTrace = [np.array([]), np.array([])]
    #     self.signal_index = {
    #         'Ch1 - Data': 0,
    #         'Ch2 - Data': 1,
    #         'FFT - Data': 0}
    #     # add single-frequency values
    #     for n in range(9):
    #         self.signal_index['FFT - Value %d' % (n+1)] = 0
    #     self.dt = 1.0
    #     # open connection
    #     boardId = int(self.comCfg.address)
    #     timeout = self.dComCfg['Timeout']
    #     self.dig = AlazarDig.AlazarTechDigitizer(
    #         systemId=1, boardId=boardId, timeout=timeout)
    #     self.dig.testLED()
    #     options = []
    #     if self.dig.fft_enabled:
    #         options.append('FFT')
    #     self.setInstalledOptions(options)


    # def performClose(self, bError=False, options={}):
    #     """Perform the close instrument connection operation"""
    #     # try to remove buffers
    #     try:
    #         self.dig.removeBuffersDMA()
    #     except:
    #         pass
    #     # remove digitizer object
    #     del self.dig


    # def performSetValue(self, quant, value, sweepRate=0.0, options={}):
    #     """Perform the Set Value instrument operation. This function should
    #     return the actual value set by the instrument"""
    #     # start with setting current quant value
    #     quant.setValue(value) 
    #      # don't do anything until all options are set, then set complete config
    #     if self.isFinalCall(options):
    #         self.setConfiguration()
    #     return value


    # def performGetValue(self, quant, options={}):
    #     """Perform the Get Value instrument operation"""
    #     # only implmeneted for traces
    #     if quant.name in self.signal_index:
    #         # special case for hardware looping
    #         if self.isHardwareLoop(options):
    #             return self.getSignalHardwareLoop(quant, options)
    #         # check if first call, if so get new traces
    #         if self.isFirstCall(options):
    #             # clear trace buffer
    #             self.lTrace = [np.array([]), np.array([])]
    #             # read traced to buffer, proceed depending on model
    #             if self.getModel() in ('9870',):
    #                 self.getTracesNonDMA()
    #             else:
    #                 self.getTracesDMA(hardware_trig=self.isHardwareTrig(options))
    #         value = self.extract_trace_value(quant)
    #     else:
    #         # just return the quantity value
    #         value = quant.getValue()
    #     return value


    # def performArm(self, quant_names, options={}):
    #     """Perform the instrument arm operation"""
    #     # arming is only implemented for DMA reaoud
    #     if self.getModel() in ('9870',):
    #         return
    #     # make sure we are arming for reading traces, if not return
    #     signals = [name in self.signal_index for name in quant_names]
    #     if not np.any(signals):
    #         return
    #     # get config
    #     bGetCh1 = bool(self.getValue('Ch1 - Enabled'))
    #     bGetCh2 = bool(self.getValue('Ch2 - Enabled'))
    #     nSample = int(self.getValue('Number of samples'))
    #     nRecord = int(self.getValue('Number of records'))
    #     nAverage = int(self.getValue('Number of averages'))
    #     nBuffer = int(self.getValue('Records per Buffer'))
    #     nMemSize = int(self.getValue('Max buffer size'))
    #     nMaxBuffer = int(self.getValue('Max number of buffers'))
    #     fft_config = self.get_fft_config()
    #     if (not bGetCh1) and (not bGetCh2):
    #         return
    #     # configure and start acquisition
    #     if self.isHardwareLoop(options):
    #         # in hardware looping, number of records is set by the hardware looping
    #         (seq_no, n_seq) = self.getHardwareLoopIndex(options)
    #         # disable trig timeout (set to 3 minutes)
    #         self.dig.AlazarSetTriggerTimeOut(self.dComCfg['Timeout'] + 180.0)
    #         # need to re-configure the card since record size was not known at config
    #         self.dig.readTracesDMA(bGetCh1, bGetCh2, nSample, n_seq, nBuffer, nAverage,
    #                                bConfig=True, bArm=True, bMeasure=False, 
    #                                bufferSize=nMemSize, maxBuffers=nMaxBuffer,
    #                                fft_config=fft_config)
    #     else:
    #         # if not hardware looping, just trig the card, buffers are already configured 
    #         self.dig.readTracesDMA(bGetCh1, bGetCh2, nSample, nRecord, nBuffer, nAverage,
    #                                bConfig=False, bArm=True, bMeasure=False,
    #                                bufferSize=nMemSize, maxBuffers=nMaxBuffer,
    #                                fft_config=fft_config)


    # def _callbackProgress(self, progress):
    #     """Report progress to server, as text string"""
    #     s = 'Acquiring traces (%.0f%%)' % (100*progress)
    #     self.reportStatus(s)


    # def getSignalHardwareLoop(self, quant, options):
    #     """Get data from round-robin type averaging"""
    #     (seq_no, n_seq) = self.getHardwareLoopIndex(options)
    #     # if first sequence call, get data
    #     if seq_no == 0 and self.isFirstCall(options):
    #         bGetCh1 = bool(self.getValue('Ch1 - Enabled'))
    #         bGetCh2 = bool(self.getValue('Ch2 - Enabled'))
    #         nSample = int(self.getValue('Number of samples'))
    #         nAverage = int(self.getValue('Number of averages'))
    #         nBuffer = int(self.getValue('Records per Buffer'))
    #         nMemSize = int(self.getValue('Max buffer size'))
    #         nMaxBuffer = int(self.getValue('Max number of buffers'))
    #         fft_config = self.get_fft_config()
    #         # show status before starting acquisition
    #         self.reportStatus('Digitizer - Waiting for signal')
    #         # get data
    #         (vCh1, vCh2) = self.dig.readTracesDMA(bGetCh1, bGetCh2,
    #                        nSample, n_seq, nBuffer, nAverage,
    #                        bConfig=False, bArm=False, bMeasure=True,
    #                        funcStop=self.isStopped,
    #                        funcProgress=self._callbackProgress,
    #                        firstTimeout=self.dComCfg['Timeout']+180.0,
    #                        bufferSize=nMemSize,
    #                        maxBuffers=nMaxBuffer,
    #                        fft_config=fft_config)
    #         # re-shape data and place in trace buffer
    #         nSample = len(vCh1) / n_seq
    #         self.lTrace[0] = vCh1.reshape((n_seq, nSample))
    #         self.lTrace[1] = vCh2.reshape((n_seq, nSample))
    #     # after getting data, pick values to return
    #     value = self.extract_trace_value(quant, seq_no)
    #     return value


    # def setConfiguration(self):
    #     """Set digitizer configuration based on driver settings"""
    #     # clock configuration
    #     SourceId = int(self.getCmdStringFromValue('Clock source'))
    #     if self.getValue('Clock source') == 'Internal':
    #         # internal
    #         SampleRateId = int(self.getCmdStringFromValue('Sample rate'),0)
    #         lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
    #                  1E6, 2E6, 5E6, 10E6, 20E6, 50E6, 100E6, 200E6, 500E6, 1E9,
    #                  1.2E9, 1.5E9, 2E9, 2.4E9, 3E9, 3.6E9, 4E9]
    #         Decimation = 0
    #     elif self.getValue('Clock source') == '10 MHz Reference' and self.getModel() in ('9373','9360'):
    #         # 10 MHz ref, for 9373 - decimation is 1
    #         #for now don't allow DES mode; talk to Simon about best implementation
    #         lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
    #                  1E6, 2E6, 5E6, 10E6, 20E6, 50E6, 100E6, 200E6, 500E6, 1E9,
    #                  1.2E9, 1.5E9, 2E9, 2.4E9, 3E9, 3.6E9, 4E9]
    #         SampleRateId = int(lFreq[self.getValueIndex('Sample rate')])
    #         Decimation = 0
    #     else:
    #         # 10 MHz ref, use 1GHz rate + divider. NB!! divide must be 1,2,4, or mult of 10 
    #         SampleRateId = int(1E9)
    #         lFreq = [1E3, 2E3, 5E3, 10E3, 20E3, 50E3, 100E3, 200E3, 500E3,
    #                  1E6, 2E6, 5E6, 10E6, 20E6, 50E6, 100E6, 250E6, 500E6, 1E9]
    #         Decimation = int(round(1E9/lFreq[self.getValueIndex('Sample rate')]))
    #     self.dig.AlazarSetCaptureClock(SourceId, SampleRateId, 0, Decimation)
    #     # define time step from sample rate
    #     self.dt = 1/lFreq[self.getValueIndex('Sample rate')]
    #     # 
    #     # configure inputs
    #     for n in range(2):
    #         if self.getValue('Ch%d - Enabled' % (n+1)):
    #             # coupling and range
    #             if self.getModel() in ('9373', '9360'):
    #                 # these options are not available for these models, set to default
    #                 Coupling = 2
    #                 InputRange = 7
    #                 Impedance = 2
    #             else:
    #                 Coupling = int(self.getCmdStringFromValue('Ch%d - Coupling' % (n+1)))
    #                 InputRange = int(self.getCmdStringFromValue('Ch%d - Range' % (n+1)))
    #                 Impedance = int(self.getCmdStringFromValue('Ch%d - Impedance' % (n+1)))
    #             #set coupling, input range, impedance
    #             self.dig.AlazarInputControl(n+1, Coupling, InputRange, Impedance)
    #             # bandwidth limit, only for model 9870
    #             if self.getModel() in ('9870',):
    #                 BW = int(self.getValue('Ch%d - Bandwidth limit' % (n+1)))
    #                 self.dig.AlazarSetBWLimit(n+1, BW)
    #     # 
    #     # configure trigger
    #     Source = int(self.getCmdStringFromValue('Trig source'))
    #     Slope = int(self.getCmdStringFromValue('Trig slope'))
    #     Delay = self.getValue('Trig delay')
    #     timeout = self.dComCfg['Timeout']
    #     # trig level is relative to full range
    #     trigLevel = self.getValue('Trig level')
    #     vAmp = np.array([4, 2, 1, 0.4, 0.2, 0.1, .04], dtype=float)
    #     if self.getValue('Trig source') == 'Channel 1':
    #         maxLevel = vAmp[self.getValueIndex('Ch1 - Range')]
    #     elif self.getValue('Trig source') == 'Channel 2':
    #         maxLevel = vAmp[self.getValueIndex('Ch2 - Range')]
    #     elif self.getValue('Trig source') == 'External':
    #         if self.getModel() in ('9373', '9360'):
    #             maxLevel = 2.5
    #             ExtTrigRange = 3
    #         else:
    #             maxLevel = 5.0
    #             ExtTrigRange = 0
    #     elif self.getValue('Trig source') == 'Immediate':
    #         maxLevel = 5.0
    #         # set timeout to very short with immediate triggering
    #         timeout = 0.001
    #     # convert relative level to U8
    #     if abs(trigLevel)>maxLevel:
    #         trigLevel = maxLevel*np.sign(trigLevel)
    #     Level = int(128 + 127*trigLevel/maxLevel)
    #     # set config
    #     self.dig.AlazarSetTriggerOperation(0, 0, Source, Slope, Level)
    #     # 
    #     # config external input, if in use
    #     if self.getValue('Trig source') == 'External':
    #         Coupling = int(self.getCmdStringFromValue('Trig coupling'))
    #         self.dig.AlazarSetExternalTrigger(Coupling, ExtTrigRange)
    #     # 
    #     # set trig delay and timeout
    #     Delay = int(self.getValue('Trig delay')/self.dt)
    #     self.dig.AlazarSetTriggerDelay(Delay)
    #     self.dig.AlazarSetTriggerTimeOut(time=timeout)
    #     # config memeory buffers, only possible for cards using DMA read
    #     if self.getModel() not in ('9360', '9373'):
    #         return
    #     bGetCh1 = bool(self.getValue('Ch1 - Enabled'))
    #     bGetCh2 = bool(self.getValue('Ch2 - Enabled'))
    #     nPostSize = int(self.getValue('Number of samples'))
    #     nRecord = int(self.getValue('Number of records'))
    #     nAverage = int(self.getValue('Number of averages'))
    #     nBuffer = int(self.getValue('Records per Buffer'))
    #     nMemSize = int(self.getValue('Max buffer size'))
    #     nMaxBuffer = int(self.getValue('Max number of buffers'))
    #     fft_config = self.get_fft_config()
    #     # set ignore error flag
    #     self.dig.ignore_buffer_overflow = bool(
    #         self.getValue('Ignore buffer overflow'))
    #     # configure DMA read
    #     self.dig.readTracesDMA(bGetCh1, bGetCh2,
    #                            nPostSize, nRecord, nBuffer, nAverage,
    #                            bConfig=True, bArm=False, bMeasure=False,
    #                            bufferSize=nMemSize,
    #                            maxBuffers=nMaxBuffer,
    #                            fft_config=fft_config)


    # def getTracesDMA(self, hardware_trig=False):
    #     """Resample the data for units with DMA"""
    #     # get channels in use
    #     bGetCh1 = bool(self.getValue('Ch1 - Enabled'))
    #     bGetCh2 = bool(self.getValue('Ch2 - Enabled'))
    #     nPostSize = int(self.getValue('Number of samples'))
    #     nRecord = int(self.getValue('Number of records'))
    #     nAverage = int(self.getValue('Number of averages'))
    #     nBuffer = int(self.getValue('Records per Buffer'))
    #     nMemSize = int(self.getValue('Max buffer size'))
    #     nMaxBuffer = int(self.getValue('Max number of buffers'))
    #     fft_config = self.get_fft_config()
    #     # in hardware trig mode, there is no noed to re-arm the card
    #     bArm = not hardware_trig
    #     # get data
    #     self.lTrace[0], self.lTrace[1] = self.dig.readTracesDMA(
    #         bGetCh1, bGetCh2,
    #         nPostSize, nRecord, nBuffer, nAverage,
    #         bConfig=False, bArm=bArm, bMeasure=True,
    #         funcStop=self.isStopped,
    #         bufferSize=nMemSize,
    #         maxBuffers=nMaxBuffer,
    #         fft_config=fft_config)


    # def getTracesNonDMA(self):
    #     """Resample the data"""
    #     # get channels in use
    #     bGetCh1 = bool(self.getValue('Ch1 - Enabled'))
    #     bGetCh2 = bool(self.getValue('Ch2 - Enabled'))
    #     nPreSize = int(self.getValue('Pre-trig samples'))
    #     nPostSize = int(self.getValue('Number of samples'))
    #     nRecord = int(self.getValue('Number of records'))
    #     nAverage = int(self.getValue('Number of averages'))
    #     nBuffer = int(self.getValue('Records per Buffer'))
    #     if (not bGetCh1) and (not bGetCh2):
    #         return
        
    #     self.dig.AlazarSetRecordSize(nPreSize, nPostSize)
    #     self.dig.AlazarSetRecordCount(nRecord, nAverage)
    #     # start aquisition
    #     self.dig.AlazarStartCapture()
    #     nTry = self.dComCfg['Timeout']/0.05
    #     while nTry>0 and self.dig.AlazarBusy() and not self.isStopped():
    #         # sleep for a while to save resources, then try again
    #         self.wait(0.050)
    #         nTry -= 1
    #     # check if timeout occurred
    #     if nTry <= 0:
    #         self.dig.AlazarAbortCapture()
    #         raise Error('Acquisition timed out')
    #     # check if user stopped
    #     if self.isStopped():
    #         self.dig.AlazarAbortCapture()
    #         return
    #     #
    #     # read data for channels in use
    #     if bGetCh1:
    #         self.lTrace[0] = self.dig.readTraces(1)
    #     if bGetCh2:
    #         self.lTrace[1] = self.dig.readTraces(2)

    # def get_fft_config(self):
    #     """Get FFT configuration in format suitable for Alazartech settings"""
    #     d = {}
    #     d['enabled'] = self.dig.fft_enabled and self.getValue('FFT - Enabled')
    #     d['window'] = self.getValueIndex('FFT - Window')
    #     d['output'] = int(self.getCmdStringFromValue('FFT - Output'))
    #     # get frequency
    #     n_sample = int(self.getValue('Number of samples'))
    #     fft_length = 1
    #     while fft_length < n_sample:
    #         fft_length *= 2
    #     d['df'] = 1 / (self.dt*fft_length)
    #     return d

    # def extract_trace_value(self, quant, record=None):
    #     """Get value from traces, either as pure data, fft, or fft value
        
    #     Parameters
    #     ----------
    #     quant : Quantity
    #         Quantity to extract
    #     record : int, optional
    #         Record to get, by default None
    #     """
    #     indx = self.signal_index[quant.name]
    #     # return correct data
    #     fft_config = self.get_fft_config()
    #     dt = fft_config['df'] if fft_config['enabled'] else self.dt
    #     if record is None:
    #         value = quant.getTraceDict(self.lTrace[indx], dt=dt)
    #     else:
    #         value = quant.getTraceDict(self.lTrace[indx][record], dt=dt)
    #     if quant.name.startswith('FFT - Value'):
    #         if not fft_config['enabled']:
    #             return 0.0
    #         indx_fft = int(quant.name.split('FFT - Value ')[1])
    #         freq = self.getValue('FFT - Frequency %d' % indx_fft)
    #         # find closest frequency
    #         (fx, fy) = quant.getTraceXY(value)
    #         interp1 = interp1d(
    #             fx, fy, kind='linear', copy=False, assume_sorted=True)
    #         value = float(interp1(freq))
    #     return value


if __name__ == '__main__':
    pass
