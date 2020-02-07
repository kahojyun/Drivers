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

__version__ = "0.3.0"

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
        self.setModel(self.get_board_model())
        if self.getModel() in ('ATS9870'):
            # ATS9870 doesn't support on-board FFT
            self.setInstalledOptions([])
        memorySize_samples, bitsPerSample = self.board.getChannelInfo()
        self.bitsPerSample = bitsPerSample.value
        self.bytesPerSample = (self.bitsPerSample + 7) // 8
        self.buffers = []
        # if True, need to configure or arm
        self.bConfig = True

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        # Will cause bluescreen if somehow forget to abort acquisition :)
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
            nSample = int(self.getValue('Number of samples'))
            nAverage = int(self.getValue('Number of averages'))
            ch1 = self.getValue('Ch1 - Enabled')
            ch2 = self.getValue('Ch2 - Enabled')
            # Set nRecord accordingly and check if need measure new traces.
            bNeedMeasure = False
            if self.isHardwareLoop(options):
                i, n_pts = self.getHardwareLoopIndex(options)
                nRecord = n_pts
                if i == 0 and self.isFirstCall(options):
                    bNeedMeasure = True
            else:
                nRecord = int(self.getValue('Number of records'))
                if self.isFirstCall(options):
                    bNeedMeasure = True
            if bNeedMeasure:
                try:
                    # If not hardware trig, arm before acquiring
                    if not self.isHardwareTrig(options):
                        self.arming(nRecord, nAverage)
                    buffer_callback, post_process = self.get_averager(nRecord, nAverage)
                    bTrig = self.isHardwareTrig(options)
                    self.acquire_data(buffer_callback, post_process, bTrig)
                finally:
                    self.board.abortAsyncRead()
                self.lTrace = [np.zeros(nSample*nRecord), np.zeros(nSample*nRecord)]
                # Mutiply channel range, remove extra data
                if ch1 and ch2:
                    rs = self.vData.reshape(nRecord, -1, 2)
                    self.lTrace[0] = self.channel_range[0] * rs[:, :nSample, 0].flatten()
                    self.lTrace[1] = self.channel_range[1] * rs[:, :nSample, 1].flatten()
                elif ch1:
                    rs = self.vData.reshape(nRecord, -1)
                    self.lTrace[0] = self.channel_range[0] * rs[:, :nSample].flatten()
                elif ch2:
                    rs = self.vData.reshape(nRecord, -1)
                    self.lTrace[1] = self.channel_range[1] * rs[:, :nSample].flatten()
                if self.isHardwareLoop(options):
                    self.lTrace[0].shape = (nRecord, -1)
                    self.lTrace[1].shape = (nRecord, -1)
            if self.isHardwareLoop(options):
                value = quant.getTraceDict(self.lTrace[self.signal_index[quant.name]][i],
                                            dx=1/self.getValue('Sample rate'))
            else:
                value = quant.getTraceDict(self.lTrace[self.signal_index[quant.name]],
                                            dx=1/self.getValue('Sample rate'))
        else:
            # Unable to get configuaration from board. Return stored values.
            value = quant.getValue()
        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        # check quant names, arm if want traces
        if not np.any([name in self.signal_index.keys() for name in quant_names]):
            return
        if self.isHardwareLoop(options):
            i, n_pts = self.getHardwareLoopIndex(options)
            nRecord = n_pts
        else:
            nRecord = int(self.getValue('Number of records'))
        nAverage = int(self.getValue('Number of averages'))
        self.arming(nRecord, nAverage)

    def get_board_model(self):
        modelId = self.board.getBoardKind()
        try:
            return ats.boardNames[modelId]
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
            self.setValue('Sample rate', sr/deci)
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
        if not self.bConfig:
            return
        self.validate_settings()
        model = self.getModel()
        # should be correct after validation
        sample_rate = self.getValue('Sample rate')
        if self.getValue('Clock source') == 'Internal':
            source = ats.INTERNAL_CLOCK
            sr_id = atsh.choose_internal_sample_rate(model, sample_rate)
            sampleRateOrId = getattr(ats, sr_id)
            decimation = 0
        else:
            source = ats.EXTERNAL_CLOCK_10MHz_REF
            sampleRateOrId, decimation = (
                atsh.choose_external_sample_rate(model, sample_rate))
        # Retry setting capture clock. Avoid 'PLL not locked' error.
        n = 0
        retry = 5
        while not self.isStopped():
            n += 1
            try:
                self.board.setCaptureClock(source,
                                    sampleRateOrId,
                                    ats.CLOCK_EDGE_RISING,
                                    decimation)
            except Exception as e:
                if n > retry:
                    raise e
                time.sleep(1)
                continue
            break

        self.channelCount = 0
        self.channel_range = [0.4, 0.4]
        for n in range(2):
            ch = n+1
            if self.getValue(f'Ch{ch} - Enabled'):
                self.channelCount += 1
                # TODO: Select input parameters as required.
                coupling = self.getCmdStringFromValue(f'Ch{ch} - Coupling')
                input_range = self.getCmdStringFromValue(f'Ch{ch} - Range')
                self.channel_range[n] = atsh.INPUT_RANGE_VALUE[input_range]
                impedance = self.getCmdStringFromValue(f'Ch{ch} - Impedance')
                self.board.inputControlEx(ats.channels[n],
                                    getattr(ats, coupling),
                                    getattr(ats, input_range),
                                    getattr(ats, impedance))
                # seems not supported by ATS9870
                # if self.getModel() in ('ATS9870'):
                #     # TODO: Select bandwidth limit as required.
                #     bw_limit = int(self.getValue(f'Ch{ch} - Bandwidth limit'))
                #     self.board.setBWLimit(ats.channels[n], bw_limit)
        
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
        # Sample clock before decimation
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
        # Calculate timeout ticks. A tick is 10 us
        triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
        self.board.setTriggerTimeOut(triggerTimeout_clocks)

        # Configure AUX I/O connector as required
        self.board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                            0)
        
        # records to be omitted
        self.nIgnoreTrig = int(self.getValue('Ignore Trig'))
        self.log('Finish board configuration.')
        self.bConfig = False

    def plan_acquisition(self, nRecord=1, nAverage=1):
        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0

        # TODO: Select the number of samples per record.
        REC_SIZE_RES = atsh.HARDWARE_SPEC['REC_SIZE_RES'][self.getModel()]
        MIN_REC_SIZE = atsh.HARDWARE_SPEC['MIN_REC_SIZE'][self.getModel()]
        nSample = int(self.getValue('Number of samples'))
        postTriggerSamples = int(np.ceil(nSample/REC_SIZE_RES)*REC_SIZE_RES)
        postTriggerSamples = max(postTriggerSamples, MIN_REC_SIZE)

        # TODO: Select the active channels.
        channelCount = self.channelCount

        # Compute the number of bytes per record
        bytesPerSample = self.bytesPerSample
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord

        # TODO: Select the number of records per DMA buffer.
        nTotal = nRecord*nAverage + self.nIgnoreTrig
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
        bytesPerBuffer = bytesPerRecord * self.recordsPerBuffer * self.channelCount
        # Return if buffer size doesn't change
        if len(self.buffers) != 0 and self.buffers[0].size_bytes == bytesPerBuffer:
            return

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

    def arming(self, nRecord, nAverage):
        self.board.abortAsyncRead()
        self.configure_board()
        self.plan_acquisition(nRecord, nAverage)
        self.prepare_buffer()
        
        # Set the record size. No pre-trigger samples.
        self.board.setRecordSize(0, self.samplesPerRecord)

        recordsPerAcquisition = self.recordsPerBuffer * self.buffersPerAcquisition
        channels = 0
        for i in range(2):
            if self.getValue(f'Ch{i+1} - Enabled'):
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

    def get_averager(self, nRecord, nAverage):
        self.vData = np.zeros(self.samplesPerRecord*nRecord*self.channelCount, dtype=np.float)
        self.nRecordCompleted = 0
        self.nRecordIgnored = 0
        def averager(data, nRecord, nAverage):
            recPerBuf = self.recordsPerBuffer
            sPerRec = self.samplesPerRecord
            recComp = self.nRecordCompleted
            channelCount = self.channelCount
            nTotal = nRecord * nAverage
            # omit first records
            if self.nRecordIgnored < self.nIgnoreTrig:
                recIgn = self.nIgnoreTrig - self.nRecordIgnored
                if recPerBuf <= recIgn:
                    self.nRecordIgnored += recPerBuf
                    return
                data = data[sPerRec*recIgn*channelCount:]
                recPerBuf -= recIgn
                self.nRecordIgnored = self.nIgnoreTrig
            # drop extra data
            if recComp + recPerBuf > nTotal:
                recPerBuf = nTotal - recComp
                data = data[:sPerRec*recPerBuf*channelCount]
            pos = (recComp % nRecord)*sPerRec*channelCount
            if pos + len(data) <= len(self.vData):
                self.vData[pos: pos+len(data)] += data
            else:
                if pos > 0:
                    pre = len(self.vData) - pos
                    self.vData[pos:] += data[:pre]
                else:
                    pre = 0
                post = (len(data) - pre) % len(self.vData)
                if post > 0:
                    self.vData += np.sum(data[pre: -post].reshape(-1, len(self.vData)), dtype=np.float, axis=0)
                    self.vData[:post] += data[-post:]
                else:
                    self.vData += np.sum(data[pre:].reshape(-1, len(self.vData)), dtype=np.float, axis=0)
            self.nRecordCompleted += recPerBuf
        def post_process(nAverage):
            bitsPerSample = self.bitsPerSample
            #  Right-shift raw data to get sample code
            bitShift = (-bitsPerSample) % 8
            codeZero = (1 << (bitsPerSample - 1)) - 0.5
            codeZero *= 1 << bitShift
            codeRange = (1 << (bitsPerSample - 1)) - 0.5
            codeRange *= 1 << bitShift
            self.vData = ((self.vData / nAverage) - codeZero) / codeRange
        return lambda x: averager(x, nRecord, nAverage), lambda: post_process(nAverage)
        
    def acquire_data(self, process_buffer, post_process, trig_mode=False):
        timeout = self.getValue('Timeout')
        first_timeout = self.getValue('First timeout')
        t_out = first_timeout if trig_mode else timeout
        start = time.perf_counter() # Keep track of when acquisition started
        try:
            buffersCompleted = 0
            # bytesTransferred = 0
            # temp = np.zeros((self.buffersPerAcquisition, len(self.buffers[0].buffer)), dtype=np.uint8)
            # process_time = 0
            while (buffersCompleted < self.buffersPerAcquisition and not
                self.isStopped()):
                # Wait for the buffer at the head of the list of available
                # buffers to be filled by the board.
                buffer = self.buffers[buffersCompleted % len(self.buffers)]
                self.board.waitAsyncBufferComplete(buffer.addr, timeout_ms=int(t_out*1000))
                t_out = timeout
                buffersCompleted += 1
                # bytesTransferred += buffer.size_bytes

                # TODO: Process sample data in this buffer. Data is available
                # as a NumPy array at buffer.buffer
                # process_start = time.perf_counter()
                process_buffer(buffer.buffer)
                # process_stop = time.perf_counter()
                # process_time += process_stop-process_start
                # self.log(f'buffer #:{buffersCompleted}, process time:{process_stop-process_start}')
                progress = 100*buffersCompleted/self.buffersPerAcquisition
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
        post_process()
        transferTime_sec = time.perf_counter() - start
        self.log("Capture completed in %f sec" % transferTime_sec)
        # process_time = time.perf_counter()
        # for i in range(self.buffersPerAcquisition):
        #     process_buffer(temp[i])
        # process_time = time.perf_counter() - process_time
        # self.log(f'Buffer process time: {process_time} sec')
        # buffersPerSec = 0
        # bytesPerSec = 0
        # recordsPerSec = 0
        # if transferTime_sec > 0:
        #     buffersPerSec = buffersCompleted / transferTime_sec
        #     bytesPerSec = bytesTransferred / transferTime_sec
        #     recordsPerSec = self.recordsPerBuffer * buffersCompleted / transferTime_sec
        # self.log("Captured %d buffers (%f buffers per sec)" %
        #     (buffersCompleted, buffersPerSec))
        # self.log("Captured %d records (%f records per sec)" %
        #     (self.recordsPerBuffer * buffersCompleted, recordsPerSec))
        # self.log("Transferred %d bytes (%f bytes per sec)" %
        #     (bytesTransferred, bytesPerSec))

if __name__ == '__main__':
    pass
