import ctypes
from datetime import date
from enum import IntEnum, unique
from io import IOBase, BytesIO
from typing import List

import numpy as np


# General notes from the XTF format document (rev35)
# 1. All structures should be zero-filled before use.
# 2. Unused values should remain zero.
# 3. File header is a multiple of 1024 bytes (1024 added for each multiple of 6 channels)

"""
XTF Data types - nbytes:
char    - 1 (signed)
short   - 2 (signed)
int     - * (signed) OS dependent size
long    - 4 (signed)
float   - 4
double  - 8
BYTE    - 1 (unsigned)
WORD    - 2 (unsigned)
DWORD   - 4 (unsigned)
Hex     - 0x0
"""

#region Enumerations

# Mapping from number of bytes to the unsigned numpy type
xtf_dtype = {
    1: np.uint8,
    2: np.uint16,
    4: np.uint32,
    8: np.uint64
}

class AutoIntEnum(IntEnum):
    """
    Enumeration that automatically increments subsequent elements.
    """
    def __new__(cls):
        value = len(cls.__members__)
        obj = int.__new__(cls)
        obj._value_ = value
        return obj

@unique
class XTFChannelType(AutoIntEnum):
    subbottom = ()
    port = ()
    stbd = ()
    bathy = ()

@unique
class XTFNavUnits(IntEnum):
    meters = 0
    latlong = 3

@unique
class XTFHeaderType(IntEnum):
    """
    The types of headers.
    """
    sonar = 0                           # Sidescan and subbottom-profiler
    notes = 1                           # Text notes
    bathy = 2                           # Bathymetry data
    attitude = 3                        # Attitude packet (pitch, roll, heave, yaw)
    forward = 4                         # Forward-look data
    elac = 5                            # Elac raw data packet (multibeam)
    raw_serial = 6                      # Raw data from serial port (ASCII)
    embed_head = 7                      # Embedded header record - num samples probably
    hidden_sonar = 8                    # Redundant (overlapping) ping from Klein 5000
    seaview_processed_bathy = 9         # Bathymetry (angles) for Seaview
    seaview_depths = 10                 # Bathymetry from Seaview data (depths)
    rsvd_highspeed_sensor = 11          # Used by Klein, 0=roll, 1=yaw
    echostrength = 12                   # Elac EchoStrength (10 values)
    georec = 13                         # Used to store mosaic parameters
    klein_raw_bathy = 14                # Bathymetry data from te Klein 5000
    highspeed_sensor2 = 15              # High speed sensor from Klein 5000
    elac_xse = 16                       # Elac dual-head
    bathy_xyza = 17
    k5000_bathy_iq = 18                 # Raw IQ data from Klein 5000 server
    bathy_snippet = 19
    gps = 20
    gps_statistics = 21
    single_beam = 22
    gyro = 23                           # Heading/speed sensor
    trackpoint = 24
    multibeam = 25
    q_singlebeam = 26
    q_multitx = 27
    q_multibeam = 28
    navigation = 42                     # Source time-stamped navigation data, holds updates of any nav data
    time = 50
    benthos_caati_sara = 60             # Custom Benthos data
    header_7125 = 61                    # 7125 bathy data
    header_7125_snippet = 62            # 7125 Bathy data snippets
    qinsy_r2sonic_bathy = 65            # QINSy R2Sonic bathy data
    qinsy_r2sonic_fts = 66              # QINSy R2Sonic bathy footprint time series (snippets)
    r2sonic_bathy = 68                  # Triton R2Sonic bathy data
    r2sonic_fts = 69                    # Triton R2sonic footprint time series
    coda_echoscope_data = 70            # Custom CODA Echoscope data
    coda_echoscope_config = 71          # Custom CODA Echoscope config
    coda_echoscope_image = 72           # Custom CODA Echoscope image
    edgetech_4600 = 73
    multibeam_raw_beam_angle = 74       # Note: Unsure if this is the correct name for this header-type
    sourcetime_gyro = 84                # Note: XTF_HEADER_GYRO is defined as 23 (difference is receive/source time)
    reson_position = 100                # Raw position packet, reserved for use by Reson, Inc. RESON ONLY
    bathy_proc = 102
    attitude_proc = 103
    singlebeam_proc = 104
    aux_proc = 105                      # Aux channel + aux altitude + magnetometer
    pos_raw_navigation = 107
    kleinv4_data_page = 108
    custom_vendor_data = 199
    user_defined = 200


class XTFManufacturerID(AutoIntEnum):
    unknown = ()
    benthos = ()
    reson = ()
    edgetech = ()
    klein = ()
    coda = ()
    kongsberg = ()
    cmax = ()
    marine_sonics = ()
    applied_signal = ()
    imagenex = ()
    geoacoustics = ()


class XTFSonarType(AutoIntEnum):
    none = ()
    jamstec = ()
    analog_c31 = ()
    sis1000 = ()
    analog_32chan = ()
    klein2000 = ()
    rws = ()
    df1000 = ()
    seabat = ()
    klein595 = ()
    egg260 = ()
    sonatech_dds = ()
    echoscan = ()
    elac = ()
    klein5000 = ()
    reson_seabat_8101 = ()
    imagenex_858 = ()
    usn_silos = ()
    sonatech = ()
    delph_au32 = ()
    generic_sonar = ()
    simrad_sm2000 = ()
    standard_multimedia_audio = ()
    edgetech_aci_card = ()
    edgetech_black_box = ()
    fugro_deeptow = ()
    cc_edgetech_chirp_conversion = ()
    dti_sas = ()
    fugro_osiris_ss = ()
    fugro_osiris_mb = ()
    geoacoustics_sls = ()
    simrad_em2000_em3000 = ()
    klein_system_3000 = ()
    shrsss_chirp_system = ()
    benthos_c3d_sara_caati = ()
    edgetech_mpx = ()
    cmax = ()
    benthos_sis1624 = ()
    edgetech_4200 = ()
    benthos_sis1500 = ()
    benthos_sis1502 = ()
    benthos_sis3000 = ()
    benthos_sis7000 = ()
    df1000_dcu = ()
    none_sidescan = ()
    none_multibeam = ()
    reson_7125 = ()
    coda_echoscope = ()
    kongsberg_sas = ()
    qinsy = ()
    geoacoustics_dsss = ()
    cmax_usb = ()
    swathplus_bathy = ()
    r2sonic_qinsy = ()
    r2sonic_triton = ()
    swathplus_converted_bathy = ()
    edgetech_4600 = ()
    klein_3500 = ()
    klein_5900 = ()
    em2040 = ()
    klein5kv2 = ()
    dt100 = ()
    kraken62 = ()
    unknown1 = ()
    unknown2 = ()
    kraken65 = ()
    klein_4900 = ()
    fsi_hms622 = ()
    fsi_hms6x4 = ()
    fsi_hms6x5 = ()

assert XTFSonarType.fsi_hms6x5 != 69, 'XTFSonarType enumeration ends on incorrect number'

#endregion

#region C-Types


class XTFBase(ctypes.LittleEndianStructure):
    """
    Base class for all XTF ctypes.Structure children.
    Exposes basic utility like printing of fields and constructing class from a buffer.
    """
    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __new__(cls, buffer: IOBase = None):
        if buffer:
            if type(buffer) in [bytes, bytearray]:
                buffer = BytesIO(buffer)

            header_bytes = buffer.read(ctypes.sizeof(cls))
            if not header_bytes:
                raise RuntimeError('XTF file shorter than expected (end hit while reading {})'.format(cls.__name__))

            obj = cls.from_buffer_copy(header_bytes)
        else:
            obj = ctypes.LittleEndianStructure.__new__(cls)

        return obj

    def __str__(self):
        """
        Prints the fields in the class (with ctype-fields) in the order in which they appear in the structure.
        """
        fields = []
        for field_name in dir(self):
            if not field_name.startswith('_') and not field_name.endswith('_'):
                field_value = getattr(self, field_name)
                field_type = type(field_value)

                # callable(obj) will return true for the fields, using 'method' name instead
                if not field_type.__name__ == 'method':
                    if hasattr(self.__class__, field_name) and hasattr(getattr(self.__class__, field_name), 'offset'):
                        offset = getattr(self.__class__, field_name).offset
                    else:
                        offset = 2 ** 31

                    if ctypes.Array in field_type.__bases__ and field_type._type_ not in [ctypes.c_char, ctypes.c_wchar]:
                        out_str = '{}: {}\n'.format(field_name, list(field_value))
                    else:
                        out_str = '{}: {}\n'.format(field_name, field_value)

                    fields.append((offset, out_str))

        # Sort by offset (non-ctypes placed last)
        fields.sort(key=lambda x: x[0])
        out = ''.join(field[1] for field in fields)

        return out


class XTFChanInfo(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('TypeOfChannel', ctypes.c_uint8),
        ('SubChannelNumber', ctypes.c_uint8),
        ('CorrectionFlags', ctypes.c_uint16),
        ('UniPolar', ctypes.c_uint16),
        ('BytesPerSample', ctypes.c_uint16),
        ('Reserved', ctypes.c_uint32),
        ('ChannelName', ctypes.c_char * 16),
        ('VoltScale', ctypes.c_float),
        ('Frequency', ctypes.c_float),
        ('HorizBeamAngle', ctypes.c_float),
        ('TiltAngle', ctypes.c_float),
        ('BeamWidth', ctypes.c_float),
        ('OffsetX', ctypes.c_float),
        ('OffsetY', ctypes.c_float),
        ('OffsetZ', ctypes.c_float),
        ('OffsetYaw', ctypes.c_float),
        ('OffsetPitch', ctypes.c_float),
        ('OffsetRoll', ctypes.c_float),
        ('BeamsPerArray', ctypes.c_uint16),
        ('ReservedArea2', ctypes.c_uint8 * 54)
    ]

    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)
        if not buffer:
            self.Reserved = 1024  # For compatibility reasons with old viewers


class XTFFileHeader(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('FileFormat', ctypes.c_uint8),
        ('SystemType', ctypes.c_uint8),
        ('RecordingProgramName', ctypes.c_char * 8),
        ('RecordingProgramVersion', ctypes.c_char * 8),
        ('SonarName', ctypes.c_char * 16),
        ('SonarType', ctypes.c_uint16),
        ('NoteString', ctypes.c_char * 64),
        ('ThisFileName', ctypes.c_char * 64),
        ('NavUnits', ctypes.c_uint16),
        ('NumberOfSonarChannels', ctypes.c_uint16),
        ('NumberOfBathymetryChannels', ctypes.c_uint16),
        ('NumberOfSnippetChannels', ctypes.c_uint8),
        ('NumberOfForwardLookArrays', ctypes.c_uint8),
        ('NumberOfEchoStrengthChannels', ctypes.c_uint16),
        ('NumberOfInterferometryChannels', ctypes.c_uint8),
        ('Reserved1', ctypes.c_uint8),
        ('Reserved2', ctypes.c_uint16),
        ('ReferencePointHeight', ctypes.c_float),
        ('ProjectionType', ctypes.c_uint8 * 12),
        ('SpheriodType', ctypes.c_uint8 * 10),
        ('NavigationLatency', ctypes.c_int32),
        ('OriginY', ctypes.c_float),
        ('OriginX', ctypes.c_float),
        ('NavOffsetY', ctypes.c_float),
        ('NavOffsetX', ctypes.c_float),
        ('NavOffsetZ', ctypes.c_float),
        ('NavOffsetYaw', ctypes.c_float),
        ('MRUOffsetY', ctypes.c_float),
        ('MRUOffsetX', ctypes.c_float),
        ('MRUOffsetZ', ctypes.c_float),
        ('MRUOffsetYaw', ctypes.c_float),
        ('MRUOffsetPitch', ctypes.c_float),
        ('MRUOffsetRoll', ctypes.c_float),
        ('ChanInfo', XTFChanInfo * 6)
    ]

    sonar_chan_types = [
        XTFChannelType.port.value,
        XTFChannelType.stbd.value,
        XTFChannelType.subbottom.value]

    def channel_count(self, verbose: bool = False) -> int:
        """
        Returns the number of separate channels present in the XTF file.
        :param verbose: If true, the number of channels per channel type is printed.
        :return: The total number of channels.
        """
        if verbose:
            print('XTF Channels: sonar={}, bathy={}, snippet={}, forward={}, echo={}, interferometry={}'.format(
                self.NumberOfSonarChannels,
                self.NumberOfBathymetryChannels,
                self.NumberOfSnippetChannels,
                self.NumberOfForwardLookArrays,
                self.NumberOfEchoStrengthChannels,
                self.NumberOfInterferometryChannels)
            )

        n_channels = self.NumberOfSonarChannels \
                   + self.NumberOfBathymetryChannels \
                   + self.NumberOfSnippetChannels \
                   + self.NumberOfForwardLookArrays \
                   + self.NumberOfEchoStrengthChannels \
                   + self.NumberOfInterferometryChannels

        return n_channels

    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)

        if buffer:
            chan_info = [self.ChanInfo[i] for i in range(0, self.channel_count())]  # type: List[XTFChanInfo]
            self.sonar_info = [x for x in chan_info if x.TypeOfChannel in XTFFileHeader.sonar_chan_types]
            self.bathy_info = [x for x in chan_info if x.TypeOfChannel == XTFChannelType.bathy.value]
        else:
            self.FileFormat = 0x7B
            self.SystemType = 1
            # Set ChanInfo[i].Reserved to 1024 for compatibility reasons (used to be NumSamples)
            for i in range(0, 6):
                self.ChanInfo[i].Reserved = 1024
                self.RecordingProgramName = b'pyxtf'
                self.RecordingProgramVersion = b'223'


class XTFPacket(XTFBase):
    """
    This is base class for all packets to derive from.
    Some packets derive from the subclass XTFPacketStart instead, due to the common first fields present in many packets
    """
    _pack_ = 1
    _fields_ = []

    def __new__(cls, buffer=None, file_header=None, *args, **kwargs):
        return super().__new__(cls, buffer=buffer, *args, **kwargs)

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, *args, **kwargs)

    def get_time(self):
        # All XTF packets has the fields Year, Month, Day, Hour, Minute, Second
        # Some packets come with SourceEpoch (time since 1970-1-1) which is used if present
        # The presence of high-resolution timers vary, and will be checked for (at runtime)

        # Use epoch if available, else calculate from Year-Month-Day etc
        if hasattr(self, 'SourceEpoch') and self.SourceEpoch:
            p_time = np.datetime64(self.SourceEpoch, 's')

            # XTFAttitudeData has an additional epoch field with microseconds
            # Return immediately, as the high-precision fields added later doubles up
            if hasattr(self, 'EpochMicroseconds') and self.EpochMicroseconds:
                p_time += np.timedelta64(self.EpochMicroseconds, 'us')
                return p_time
        else:
            # Numpy does not handle leap years and varying number of days per month
            # Calculate the day from the python.datetime module
            days = (date(self.Year, self.Month, self.Day) - date(self.Year, 1, 1)).days

            # Calculate time using common fields
            p_time = np.datetime64(str(self.Year), 'Y') + \
                     np.timedelta64(days, 'D') + \
                     np.timedelta64(self.Hour, 'h') + \
                     np.timedelta64(self.Minute, 'm') + \
                     np.timedelta64(self.Second, 's')

            # Add time using high-res fields
            if hasattr(self, 'HSeconds'):
                return p_time + np.timedelta64(self.HSeconds*10, 'ms')  # HSeconds = hundredths of a second (0-99)

            if hasattr(self, 'Millisecond'):
                p_time += np.timedelta64(self.Millisecond, 'ms')

            if hasattr(self, 'Microsecond'):
                p_time += np.timedelta64(self.Microsecond, 'us')

        #print(self.Year, self.Month, self.Day, self.Hour, self.Minute, self.Second, self.Millisecond)

        return p_time


class XTFPacketStart(XTFPacket):
    """
    This is a structure representing the first few bytes in (most) of the XTF packets.
    It can be used to inspect the packet type before reading the whole header.
    """
    _pack_ = 1
    _fields_ = [
        ('MagicNumber', ctypes.c_uint16),
        ('HeaderType', ctypes.c_uint8),
        ('SubChannelNumber', ctypes.c_uint8),  # Note: For RawSerialHeader, this is SerialPort (same size)
        ('NumChansToFollow', ctypes.c_uint16),
        ('Reserved1', ctypes.c_uint16 * 2),
        ('NumBytesThisRecord', ctypes.c_uint32)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if buffer:
            if self.MagicNumber != 0xFACE:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.MagicNumber = 0xFACE
            self.HeaderType = XTFHeaderType.user_defined

    def __new__(cls, buffer=None, file_header=None, *args, **kwargs):
        return super().__new__(cls, buffer=buffer, file_header=file_header, *args, **kwargs)


class XTFAttitudeData(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Reserved2', ctypes.c_uint32 * 2),
        ('EpochMicroseconds', ctypes.c_uint32),
        ('SourceEpoch', ctypes.c_uint32),
        ('Pitch', ctypes.c_float),  # Positive value is nose up
        ('Roll', ctypes.c_float),   # Positive value is roll to starboard
        ('Heave', ctypes.c_float),  # Positive value is sensor up
        ('Yaw', ctypes.c_float),  # Positive value is turn right
        ('TimeTag', ctypes.c_uint32),
        ('Heading', ctypes.c_float),
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Millisecond', ctypes.c_uint16),
        ('Reserved3', ctypes.c_uint8)
        ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if not buffer:
            self.HeaderType = XTFHeaderType.attitude


class XTFNotesHeader(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('ReservedBytes', ctypes.c_uint8 * 35),
        ('NotesText', ctypes.c_char * 200)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if not buffer:
            self.HeaderType = XTFHeaderType.notes.value


class XTFRawSerialHeader(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('HSeconds', ctypes.c_uint8),  # Hundredths of seconds (0-99)
        ('JulianDay', ctypes.c_uint16),
        ('TimeTag', ctypes.c_uint32),  # Millisecond timer value
        ('StringSize', ctypes.c_uint16)  # After this, the number of ascii bytes follow
    ]

    # Serialport and subchannelnumber is the same variable
    # The documentation uses serialport, so this redirection is added to match the docs
    @property
    def SerialPort(self):
        return self.SubChannelNumber

    @SerialPort.setter
    def SerialPort(self, value):
        self.SubChannelNumber = value

    # Just declaration of variables to more easily generate entries in the .pyi file
    # TODO: Generate it automatically by inspecing __init__
    _typing_static_ = []
    _typing_instance_ = [
        ('SerialPort', 'ctypes.c_uint8'),
        ('RawAsciiData', 'bytes')
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if buffer:
            # TODO: Make getters/setters that updates StringSize when changed
            self.RawAsciiData = buffer.read(ctypes.sizeof(ctypes.c_char) * self.StringSize.value)
        else:
            self.HeaderType = XTFHeaderType.raw_serial.value
            self.RawAsciiData = b''


class XTFPingChanHeader(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('ChannelNumber', ctypes.c_uint16),
        ('DownsampleMethod', ctypes.c_uint16),
        ('SlandRange', ctypes.c_float),
        ('GroundRange', ctypes.c_float),
        ('TimeDelay', ctypes.c_float),
        ('TimeDuration', ctypes.c_float),
        ('SecondsPerPing', ctypes.c_float),
        ('ProcessingFlags', ctypes.c_uint16),
        ('Frequency', ctypes.c_uint16),
        ('InitialGainCode', ctypes.c_uint16),
        ('GainCode', ctypes.c_uint16),
        ('BandWidth', ctypes.c_uint16),
        ('ContactNumber', ctypes.c_uint32),
        ('ContactClassification', ctypes.c_uint16),
        ('ContactSubNumber', ctypes.c_uint8),
        ('ContactType', ctypes.c_uint8),
        ('NumSamples', ctypes.c_uint32),  # This defines the number of samples to follow
        ('MillivoltScale', ctypes.c_uint16),
        ('ContactTimeOffTrack', ctypes.c_float),
        ('ContactCloseNumber', ctypes.c_uint8),
        ('Reserved2', ctypes.c_uint8),
        ('FixedVSOP', ctypes.c_float),
        ('Weight', ctypes.c_int16),
        ('ReservedSpace', ctypes.c_uint8 * 4)
    ]


class XTFPingHeader(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('HSeconds', ctypes.c_uint8),
        ('JulianDay', ctypes.c_uint16),
        ('EventNumber', ctypes.c_uint32),
        ('PingNumber', ctypes.c_uint32),
        ('SoundVelocity', ctypes.c_float),
        ('OceanTide', ctypes.c_float),
        ('Reserved2', ctypes.c_uint32),
        ('ConductivityFreq', ctypes.c_float),
        ('TemperatureFreq', ctypes.c_float),
        ('PressureFreq', ctypes.c_float),
        ('PressureTemp', ctypes.c_float),
        ('Conductivity', ctypes.c_float),
        ('WaterTemperature', ctypes.c_float),
        ('Pressure', ctypes.c_float),
        ('ComputedSoundVelocity', ctypes.c_float),
        ('MagX', ctypes.c_float),
        ('MagY', ctypes.c_float),
        ('MagZ', ctypes.c_float),
        ('AuxVal1', ctypes.c_float),
        ('AuxVal2', ctypes.c_float),
        ('AuxVal3', ctypes.c_float),
        ('AuxVal4', ctypes.c_float),
        ('AuxVal5', ctypes.c_float),
        ('AuxVal6', ctypes.c_float),
        ('SpeedLog', ctypes.c_float),
        ('Turbidity', ctypes.c_float),
        ('ShipSpeed', ctypes.c_float),
        ('ShipGyro', ctypes.c_float),
        ('ShipYcoordinate', ctypes.c_double),
        ('ShipXcoordinate', ctypes.c_double),
        ('ShipAltitude', ctypes.c_uint16),  # Decimeters
        ('ShipDepth', ctypes.c_uint16),  # Decimeters
        ('FixTimeHour', ctypes.c_uint8),
        ('FixTimeMinute', ctypes.c_uint8),
        ('FixTimeSecond', ctypes.c_uint8),
        ('FixTimeHsecond', ctypes.c_uint8),
        ('SensorSpeed', ctypes.c_float),
        ('KP', ctypes.c_float),
        ('SensorYcoordinate', ctypes.c_double),
        ('SensorXcoordinate', ctypes.c_double),
        ('SonarStatus', ctypes.c_uint16),
        ('RangeToFish', ctypes.c_uint16),
        ('BearingToFish', ctypes.c_uint16),
        ('CableOut', ctypes.c_uint16),
        ('Layback', ctypes.c_float),
        ('CableTension', ctypes.c_float),
        ('SensorDepth', ctypes.c_float),
        ('SensorPrimaryAltitude', ctypes.c_float),
        ('SensorAuxAltitude', ctypes.c_float),
        ('SensorPitch', ctypes.c_float),
        ('SensorRoll', ctypes.c_float),
        ('SensorHeading', ctypes.c_float),
        ('Heave', ctypes.c_float),
        ('Yaw', ctypes.c_float),
        ('AttitudeTimeTag', ctypes.c_uint32),
        ('DOT', ctypes.c_float),
        ('NavFixMilliseconds', ctypes.c_uint32),
        ('ComputerClockHour', ctypes.c_uint8),
        ('ComputerClockMinute', ctypes.c_uint8),
        ('ComputerClockSecond', ctypes.c_uint8),
        ('ComputerClockHsec', ctypes.c_uint8),
        ('FishPositionDeltaX', ctypes.c_int16),
        ('FishPositionDeltaY', ctypes.c_int16),
        ('FishPositionErrorCode', ctypes.c_uint8),
        ('OptionalOffset', ctypes.c_uint32),
        ('CableOutHundredths', ctypes.c_uint8),
        ('ReservedSpace2', ctypes.c_uint8 * 6)
    ]

    # Just declaration of variables to more easily generate entries in the .pyi file
    # TODO: Generate it automatically by inspecing __init__
    _typing_static_ = []
    _typing_instance_ = [
        ('ping_chan_headers', 'List[XTFPingChanHeader]'),
        ('data', 'List[np.ndarray]')
    ]

    _bathy_header_types = [
            XTFHeaderType.bathy_xyza.value,
            XTFHeaderType.bathy.value,
            XTFHeaderType.multibeam_raw_beam_angle
        ]

    def __new__(cls, buffer: IOBase = None, file_header: XTFFileHeader = None):
        p_header = super().__new__(cls, buffer=buffer, file_header=file_header)

        p_header.ping_chan_headers = []  # type: List[XTFPingChanHeader]
        p_header.data = []  # type: List[np.ndarray]

        if buffer:
            if not file_header:
                raise RuntimeError('Initialization of XTFPingHeader from buffer requires file_header to be passed.')

            # Sonar and bathy has a different data structure following the header
            if p_header.HeaderType == XTFHeaderType.sonar:
                for i in range(0, p_header.NumChansToFollow):
                    # Retrieve XTFPingChanHeader for this channel
                    p_chan = XTFPingChanHeader(buffer=buffer)
                    p_header.ping_chan_headers.append(p_chan)

                    # Backwards-compatibility: retrive from NumSamples if possible, else use old field
                    n_samples = p_chan.NumSamples if p_chan.NumSamples > 0 else file_header.sonar_info[i].Reserved

                    # Calculate number of bytes to read
                    n_bytes = n_samples * file_header.sonar_info[i].BytesPerSample
                    n_bytes_remaining = p_header.NumBytesThisRecord - \
                                        ctypes.sizeof(XTFPingHeader) - \
                                        ctypes.sizeof(XTFPingChanHeader)
                    if n_bytes > n_bytes_remaining:
                        raise RuntimeError('Number of bytes to read exceeds the number of bytes remaining in packet.')

                    # Read the data and output as a numpy array of the specified bytes-per-sample
                    samples = buffer.read(n_samples * file_header.sonar_info[i].BytesPerSample)
                    if not samples:
                        raise RuntimeError('File ended while reading data packets (file corrupt?)')
                    samples = np.frombuffer(samples, dtype=xtf_dtype[file_header.sonar_info[i].BytesPerSample])
                    p_header.data.append(samples)

            elif p_header.HeaderType in cls._bathy_header_types:
                # Bathymetry uses the same header as sonar, but without the XTFPingChanHeaders

                # TODO: Should the sub-channel number be used to index chan_info (?)
                #sub_chan = p_header.SubChannelNumber

                # Read the data that follows
                n_bytes = p_header.NumBytesThisRecord - ctypes.sizeof(XTFPingHeader)
                samples = buffer.read(n_bytes)
                if not samples:
                    raise Exception('XTF data packets missing (file corrupt?)')

                if p_header.HeaderType == XTFHeaderType.bathy_xyza:
                    # Processed bathy data consists of repeated XTFBeamXYZA structures
                    # Note: Using a ctypes array is a _lot_ faster than constructing a list of BeamXYZA
                    num_xyza = n_bytes // ctypes.sizeof(XTFBeamXYZA)
                    xyza_array_type = XTFBeamXYZA * num_xyza
                    xyza_array_type._pack_ = 1
                    p_header.data = xyza_array_type.from_buffer_copy(samples)
                else:
                    # Return raw bathy data as numpy array (NB: in list for consistency with sonar structure)
                    # The data is vendor specific, and therefore cannot be interpreted here
                    p_header.data = [np.frombuffer(samples, dtype=np.uint8)]
            else:
                raise RuntimeError('Unknown XTFPingHeader type encountered.')

        return p_header


    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)

        if not buffer:
            self.HeaderType = XTFHeaderType.sonar.value


class XTFPosRawNavigation(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Microsecond', ctypes.c_uint16),
        ('RawYcoordinate', ctypes.c_double),
        ('RawXcoordinate', ctypes.c_double),
        ('RawAltitude', ctypes.c_double),
        ('Pitch', ctypes.c_float),
        ('Roll', ctypes.c_float),
        ('Heave', ctypes.c_float),
        ('Heading', ctypes.c_float),
        ('Reserved2', ctypes.c_uint8)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if not buffer:
            self.HeaderType = XTFHeaderType.pos_raw_navigation.value


class XTFQPSSingleBeam(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('TimeTag', ctypes.c_uint32),
        ('Id', ctypes.c_int32),
        ('SoundVelocity', ctypes.c_float),
        ('Intensity', ctypes.c_float),
        ('Quality', ctypes.c_int32),
        ('TwoWayTravelTime', ctypes.c_float),
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Millisecond', ctypes.c_uint16),
        ('Reserved2', ctypes.c_uint8 * 7)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if not buffer:
            self.HeaderType = XTFHeaderType.q_singlebeam.value


class XTFQPSMultiTXEntry(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('Id', ctypes.c_int),
        ('Intensity', ctypes.c_float),
        ('Quality', ctypes.c_int),
        ('TwoWayTravelTime', ctypes.c_float),
        ('DeltaTime', ctypes.c_float),
        ('OffsetX', ctypes.c_float),  # Number of bytes without padding (header+data)
        ('OffsetY', ctypes.c_float),
        ('OffsetZ', ctypes.c_float),
        ('Reserved', ctypes.c_float * 4)
    ]


class XTFQPSMBEEntry(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('Id', ctypes.c_int),
        ('Intensity', ctypes.c_double),
        ('Quality', ctypes.c_int),
        ('TwoWayTravelTime', ctypes.c_double),
        ('DeltaTime', ctypes.c_double),
        ('OffsetX', ctypes.c_double),  # Number of bytes without padding (header+data)
        ('OffsetY', ctypes.c_double),
        ('OffsetZ', ctypes.c_double),
        ('Reserved', ctypes.c_float * 4)
    ]


class XTFRawCustomHeader(XTFPacket):
    _pack_ = 1
    _fields_ = [
        ('MagicNumber', ctypes.c_uint16),
        ('HeaderType', ctypes.c_uint8),
        ('ManufacturerID', ctypes.c_uint8),
        ('SonarID', ctypes.c_uint16),
        ('PacketID', ctypes.c_uint16 * 2),
        ('Reserved1', ctypes.c_uint32),
        ('NumBytesThisRecord', ctypes.c_uint32),
        ('Id', ctypes.c_int32),
        ('SoundVelocity', ctypes.c_float),
        ('Intensity', ctypes.c_float),
        ('Quality', ctypes.c_int32),
        ('TwoWayTravelTime', ctypes.c_float),
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Millisecond', ctypes.c_uint16),
        ('Reserved2', ctypes.c_uint8 * 7)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if buffer:
            if self.MagicNumber != 0xFACE:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.MagicNumber = 0xFACE
            self.HeaderType = XTFHeaderType.custom_vendor_data.value


class XTFHeaderNavigation(XTFPacket):
    _pack_ = 1
    _fields_ = [
        ('MagicNumber', ctypes.c_uint16),
        ('HeaderType', ctypes.c_uint8),
        ('Reserved', ctypes.c_uint8 * 7),
        ('NumBytesThisRecord', ctypes.c_uint32),
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Microsecond', ctypes.c_uint32),
        ('SourceEpoch', ctypes.c_uint32),
        ('TimeTag', ctypes.c_uint32),
        ('RawYcoordinate', ctypes.c_double),
        ('RawXcoordinate', ctypes.c_double),
        ('RawAltitude', ctypes.c_double),
        ('TimeFlag', ctypes.c_uint8),
        ('Reserved2', ctypes.c_uint8 * 6)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if buffer:
            if self.MagicNumber != 0xFACE:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.MagicNumber = 0xFACE
            self.HeaderType = XTFHeaderType.navigation.value


class XTFHeaderGyro(XTFPacket):
    _pack_ = 1
    _fields_ = [
        ('MagicNumber', ctypes.c_uint16),
        ('HeaderType', ctypes.c_uint8),
        ('Reserved', ctypes.c_uint8 * 7),
        ('NumBytesThisRecord', ctypes.c_uint32),
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('Microsecond', ctypes.c_uint32),
        ('SourceEpoch', ctypes.c_uint32),
        ('TimeTag', ctypes.c_uint32),
        ('Gyro', ctypes.c_float),
        ('TimeFlag', ctypes.c_uint8),
        ('Reserved1', ctypes.c_uint8 * 26)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if buffer:
            if self.MagicNumber != 0xFACE:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.MagicNumber = 0xFACE
            self.HeaderType = XTFHeaderType.gyro.value


class XTFHighSpeedSensor(XTFPacketStart):
    _pack_ = 1
    _fields_ = [
        ('Year', ctypes.c_uint16),
        ('Month', ctypes.c_uint8),
        ('Day', ctypes.c_uint8),
        ('Hour', ctypes.c_uint8),
        ('Minute', ctypes.c_uint8),
        ('Second', ctypes.c_uint8),
        ('HSeconds', ctypes.c_uint8),
        ('NumSensorBytes', ctypes.c_uint32),
        ('RelativeBathyPingNum', ctypes.c_uint32),
        ('Reserved3', ctypes.c_uint8 * 34)
    ]

    def __init__(self, buffer=None, file_header=None, *args, **kwargs):
        super().__init__(buffer=buffer, file_header=file_header, *args, **kwargs)
        if not buffer:
            self.HeaderType = XTFHeaderType.highspeed_sensor2.value


class XTFBeamXYZA(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('dPosOffsetTrX', ctypes.c_double),
        ('dPosOffsetTrY', ctypes.c_double),
        ('fDepth', ctypes.c_float),
        ('dTime', ctypes.c_double),
        ('usAmpl', ctypes.c_int16),
        ('ucQuality', ctypes.c_uint8)
    ]

    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)


class SNP0(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('ID', ctypes.c_uint32),                # Identifier code. SNP0= 0x534E5030
        ('HeaderSize', ctypes.c_uint16),        # Header size, bytes
        ('DataSize', ctypes.c_uint16),          # Data size following header, bytes
        ('PingNumber', ctypes.c_uint32),        # Sequential ping number
        ('Seconds', ctypes.c_uint32),           # Time since 00:00:00 1-Jan-1970
        ('Millisec', ctypes.c_uint32),
        ('Latency', ctypes.c_uint16),           # Time from ping to output (ms)
        ('SonarID', ctypes.c_uint16 * 2),       # Least significant four bytes of ethernet address
        ('SonarModel', ctypes.c_uint16),        # Coded model number of sonar
        ('Frequency', ctypes.c_uint16),         # Sonar frequency (kHz)
        ('SSpeed', ctypes.c_uint16),            # Programmed sound velocity (m/sec)
        ('SampleRate', ctypes.c_uint16),        # A/D sample rate (samples/sec)
        ('PingRate', ctypes.c_uint16),          # Pings per second (0.001 Hz steps)
        ('Range', ctypes.c_uint16),             # Range setting (meters)
        ('Power', ctypes.c_uint16),             # Power
        ('Gain', ctypes.c_uint16),              # (b15 = auto, b14 = TVG, b6..0 = gain)
        ('PulseWidth', ctypes.c_uint16),        # Transmit pulse width (microseconds)
        ('Spread', ctypes.c_uint16),            # TVG spreading, n*log(R), 0.25dB steps
        ('Absorb', ctypes.c_uint16),            # TVG absorption, dB/km, 1dB steps
        ('Proj', ctypes.c_uint16),              # b7 = steering, b4..0 = projector type
        ('ProjWidth', ctypes.c_uint16),         # Transmit beam width along track, 0.1 deg
        ('SpacingNum', ctypes.c_uint16),        # Receiver beam spacing, numerator, degrees
        ('SpacingDen', ctypes.c_uint16),        # Receiver beam spacing, denominator
        ('ProjAngle', ctypes.c_int16),          # Projector steering, degrees*PKT_STEER_RES
        ('MinRange', ctypes.c_uint16),          # Range filter settings
        ('MaxRange', ctypes.c_uint16),          # Range filter settings
        ('MinDepth', ctypes.c_uint16),          # Depth filter settings
        ('MaxDepth', ctypes.c_uint16),          # Depth filter settings
        ('Filters', ctypes.c_uint16),           # Enabled filters, b1 = depth, b0 = range
        ('bFlags', ctypes.c_uint8 * 2),         # b0..11 spare, b12-14 snipMode, b15 RollStab, b16 RollStab enabled
        ('HeadTemp', ctypes.c_int16),           # Head temperature, 0.1C steps
        ('BeamCnt', ctypes.c_uint16)            # Number of beams
    ]

    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)
        if buffer:
            if self.ID != 0x534E5030:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.ID = 0x534E5030


class SNP1(XTFBase):
    _pack_ = 1
    _fields_ = [
        ('ID', ctypes.c_uint32),            # Identifier code. SNP1= 0x534E5031
        ('HeaderSize', ctypes.c_uint16),    # Header size, bytes
        ('DataSize', ctypes.c_uint16),      # Data size following header, bytes
        ('PingNumber', ctypes.c_uint32),    # Sequential ping number
        ('Beam', ctypes.c_uint16),          # Beam number 0 .. N-1
        ('SnipSamples', ctypes.c_uint16),   # Snippet size, samples
        ('GainStart', ctypes.c_uint16),     # Gain at start of snippet, 0.01 dB steps (0=ignore)
        ('GainEnd', ctypes.c_uint16),       # Gain at end of snippet, 0.01 dB steps (0=ignore)
        ('FragOffset', ctypes.c_uint16),    # Fragment offset, samples from ping
        ('FragSamples', ctypes.c_uint16)    # Fragment size, samples
    ]

    def __init__(self, buffer=None, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)
        if buffer:
            if self.ID != 0x534E5031:
                raise RuntimeError('XTF packet does not start with the correct identifier (0xFACE).')
        else:
            self.ID = 0x534E5031


#endregion C-Types


# Mapping from enumerated header type to the class implementation
# TODO: XTF Bathy snippets (SNP0/SNP1 etc) requires a custom implementation in xtf_read
XTFPacketClasses = {
    XTFHeaderType.sonar: XTFPingHeader,
    XTFHeaderType.bathy: XTFPingHeader,
    XTFHeaderType.bathy_xyza: XTFPingHeader,
    XTFHeaderType.attitude: XTFAttitudeData,
    XTFHeaderType.notes: XTFNotesHeader,
    XTFHeaderType.raw_serial: XTFRawSerialHeader,
    XTFHeaderType.pos_raw_navigation: XTFPosRawNavigation,
    XTFHeaderType.q_singlebeam: XTFQPSSingleBeam,
    XTFHeaderType.custom_vendor_data: XTFRawCustomHeader,
    XTFHeaderType.navigation: XTFHeaderNavigation,
    XTFHeaderType.gyro: XTFHeaderGyro,
    XTFHeaderType.sourcetime_gyro: XTFHeaderGyro,
    XTFHeaderType.highspeed_sensor2: XTFHighSpeedSensor
}


if __name__ == '__main__':
    # TODO: Move these assertions to a test routine
    header_sizes = [
        (XTFFileHeader, 1024),
        (XTFChanInfo, 128),
        (XTFAttitudeData, 64),
        (XTFNotesHeader, 256),
        (XTFRawSerialHeader, 30),
        (XTFPingHeader, 256),
        (XTFPingChanHeader, 64),
        (XTFHighSpeedSensor, 64),
        (XTFBeamXYZA, 31),
        (XTFHeaderGyro, 64),
        (SNP0, 74),
        (SNP1, 24)
    ]
    for (xtf_header, n_bytes) in header_sizes:
        assert ctypes.sizeof(xtf_header) == n_bytes, \
            "{} expected size is {} bytes, was {} bytes".format(xtf_header.__name__, n_bytes, ctypes.sizeof(xtf_header))


