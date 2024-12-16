"""Digital Appliance Simulator client"""
from numbers import Real
from typing import Any, Callable, Dict, Generic, List, Sequence, TypeVar, Union

import voluptuous as vol

from .templates import ATTR_GROUP, ATTR_MODE, ATTR_VALUE, MODE_GET, MODE_SET, RawClient

GROUP_MAIN = "main"
GROUP_DIGITAL_OUT = "digital_out"
GROUP_ANALOG_OUT = "analog_out"
GROUP_DIGITAL_POT = "digital_pot"
GROUP_FREQUENCY_OUT = "frequency_out"
GROUP_DUTY_CYCLE_OUT = "duty_cycle_out"
GROUP_DIGITAL_IN = "digital_in"
GROUP_PWM_IN = "pwm_in"
GROUP_PWM_SET_1 = "pwm_1"
GROUP_PWM_SET_2 = "pwm_2"
GROUP_SET_VOLTAGE = "set_voltage"
GROUP_READ_ADC = "read_adc"
GROUP_BOX_VERSION = "box_version"

DIGITAL_OUT_CNT = 8
ANALOG_OUT_CNT = 8
DIGITAL_POT_CNT = 6
DIGITAL_IN_CNT = 32
PWM_IN_CNT = 2
ADC_IN_CNT = 1
ANALOG_OUT_MIN_MAX = (0, (2 ** 16) - 1)
DIGITAL_POT_MIN_MAX = (0, (2 ** 8) - 1)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Optional(GROUP_MAIN): vol.Boolean(),
        vol.Optional(GROUP_DIGITAL_OUT): {
            vol.All(
                int, vol.Range(min=0, max=DIGITAL_OUT_CNT, max_included=False)
            ): vol.Boolean()
        },
        vol.Optional(GROUP_ANALOG_OUT): {
            vol.All(
                int, vol.Range(min=0, max=ANALOG_OUT_CNT, max_included=False)
            ): vol.All(
                int, vol.Range(min=ANALOG_OUT_MIN_MAX[0], max=ANALOG_OUT_MIN_MAX[1])
            )
        },
        vol.Optional(GROUP_DIGITAL_POT): {
            vol.All(
                int, vol.Range(min=0, max=DIGITAL_POT_CNT, max_included=False)
            ): vol.All(
                int, vol.Range(min=DIGITAL_POT_MIN_MAX[0], max=DIGITAL_POT_MIN_MAX[1])
            )
        },
        vol.Optional(GROUP_FREQUENCY_OUT): vol.All(int, vol.Range(min=0, max=20000)),
        vol.Optional(GROUP_DUTY_CYCLE_OUT): vol.All(int, vol.Range(min=0, max=100)),
    }
)


class DASServiceError(Exception):
    """Type to indicate the DAS service error"""


_GLT = TypeVar("_GLT")


class _GroupList(Generic[_GLT]):
    """Modified sequence faker that handles slice, int and tuple indexing.

    On get/set it offers code execution

    :param length: object length
    :param set_executor: function to execute on element change
    :param get_executor: function to execute on element query
    """

    def __init__(
        self,
        length: int,
        set_executor: Callable = None,
        get_executor: Callable = None,
    ) -> None:
        self._set_executor = (
            self.__default_setitem_executor__ if set_executor is None else set_executor
        )
        self._get_executor = (
            self.__default_getitem_executor__ if get_executor is None else get_executor
        )
        self._length = length

    def __len__(self) -> int:
        return self._length

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        item = list(range(self._length))
        value = self._get_executor(item)
        return f"{value}"

    def __iter__(self) -> _GLT:
        for i in range(self._length):
            yield self._get_executor(i)

    def __setitem__(
        self,item: Union[slice, int, tuple], value: Union[_GLT, Sequence[_GLT]]
    ) -> None:
        """Function to handle setting of particular list item

        :param item: item or set of items to be set
        :param value: value for given pin set
        """
        if isinstance(item, slice):
            item = list(range(*item.indices(self._length)))
            if not isinstance(value, list):
                value = [value] * len(item)
            else:
                pass
        elif isinstance(item, int):
            if item >= self._length or item < 0:
                raise IndexError(f"index should be in range 0-{self._length - 1}")
            item = [item]
            value = [value]
        elif isinstance(item, tuple):
            if max(item) >= self._length or min(item) < 0:
                raise IndexError(f"index should be in range 0-{self._length - 1}")
            if not isinstance(value, list):
                value = [value] * len(item)
            else:
                pass
        elif isinstance(item, list):
            if len(item) == 1:
                item.insert(0,0)
            if not isinstance(value, list):
                value = [value] * (len(item)-1)
            else:
                pass
        self._set_executor(item, value)

    def __getitem__(
        self, item: Union[slice, int, tuple]
    ) -> Union[_GLT, Sequence[_GLT]]:
        """Function to handle getting of particular list item

        :param item: item or set of items to be read
        """
        if isinstance(item, slice):
            item = list(range(*item.indices(self._length)))
        elif isinstance(item, int):
            if item >= self._length or item < 0:
                raise IndexError(f"index should be in range 0-{self._length - 1}")
            item = [item]
        elif isinstance(item, tuple):
            if max(item) >= self._length or min(item) < 0:
                raise IndexError(f"index should be in range 0-{self._length - 1}")
        value = self._get_executor(item)
        if len(item) == 1:
            return value[0]
        else:
            return value

    @staticmethod
    def __default_setitem_executor__(_0, _1) -> None:
        raise NotImplementedError("operation not supported")

    @staticmethod
    def __default_getitem_executor__(_0) -> None:
        raise NotImplementedError("operation not supported")


class DAS(RawClient):
    """Digital Appliance Simulator Client class

    :param ip: ip address of device, running DAS service
    :param port: port of DAS service

    Usage:

    >>> from tester._clients.das import DAS  # Import DAS class
    >>> # If the script is running on the same device as das_service
    >>> d = DAS('127.0.0.1', 50002)  # Create DAS instance and store it in variable b
    """

    _exception_type = DASServiceError  #:
    _service_name = "das_service"  #:

    MAIN_DEFAULT = False
    DIGITAL_OUT_DEFAULT = False
    ANALOG_OUT_DEFAULT = 2 ** 15
    DUTY_CYCLE_OUT_DEFAULT = 0
    FREQUENCY_OUT_DEFAULT = 0
    DIGITAL_IN_DEFAULT = False
    PWM_IN_DEFAULT = {"f": 0, "d": 0}

    def __init__(self, ip: str, port: int = 50002) -> None:
        """Initializes DAS instance"""
        super(DAS, self).__init__(ip, port)
        self._digital_out = _GroupList[bool](
            DIGITAL_OUT_CNT, self._set_digital_out, self._get_digital_out
        )
        self._analog_out = _GroupList[int](
            ANALOG_OUT_CNT, self._set_analog_out, self._get_analog_out
        )
        self._digital_pot = _GroupList[int](
            DIGITAL_POT_CNT, self._set_digital_pot, self._get_digital_pot
        )
        self._digital_in = _GroupList[bool](DIGITAL_IN_CNT, None, self._get_digital_in)
        self._read_pwm = _GroupList[Dict[str, int]](PWM_IN_CNT, None, self._get_pwm_in)
        
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configures DAS from configuration data

        :param config: configuration data

        Full example configuration:

        .. code-block:: yaml

            main: 1
            digital_out:
                0: true
                1: false
            analog_out:
                0: 1032
                1: 65535  # max
                2: 0  # min
            digital_pot:
                0: 10
                1: 0  # min
                2: 255  # max
            frequency_out: 200  # from 0 to 20000
            duty_cycle_out: 50  # from 0 to 100
        """
        data = PLATFORM_SCHEMA(config)
        for k, v in data.items():
            if isinstance(v, dict):
                group = getattr(self, k)
                for k1, v1 in v.items():
                    group[k1] = v1
            elif isinstance(v, Real):
                setattr(self, k, v)

    @property
    def main(self) -> bool:
        """Main relay state

        :return: main relay state

        Usage (if one prefers function API, see
        :func:`set_main<das.DAS.set_main>`):

        >>> d.main  # Get main relay state
        False
        >>> d.main = True  # Set main relay state
        >>> d.main
        True

        .. note::

            ``1/0`` or True ``True/False`` notation can be used.
        """
        return self.get_main()

    @main.setter
    def main(self, state: bool) -> None:
        """Set main switch on/off

        :param state: desired state of main switch
        """
        self.set_main(state)

    @property
    def digital_out(self) -> _GroupList[bool]:
        """Digital output states

        :return: digital output states

        Usage (if one prefers function API, see
        :func:`set_digital_out<das.DAS.set_digital_out>`):

        >>> d.digital_out[1]  # Get single digital output state
        False
        >>> d.digital_out[1] = True  # Set second digital output state
        >>> d.digital_out[0:4]   # Get a slice of digital output states
        [False, True, False, False]
        >>> d.digital_out[0,2,5,4,6] = 1  # Set multiple digital outputs to same state
        >>> d.digital_out[:]  # Get all digital output states
        [True, True, True, False, True, True, True, False]
        >>> d.digital_out[0:5] = False  # Set slice of relays to same state
        >>> d.digital_out[:]
        [False, False, False, False, False, True, True, False]
        >>> d.digital_out[:] = 0 # Set all relays to same state
        >>> d.digital_out[:]
        [False, False, False, False, False, False, False, False]
        >>> d.digital_out[1,2,3] = [True, False, True]  # Set multiple digital outputs to different states
        >>> d.digital_out[1,2,3]
        [True, False, True]

        .. note::

            ``1/0`` or True ``True/False`` notation can be used.
        .. note::

            In order to set all values or read the whole list, [:] must be used
            at the end.
        .. note::

            When setting a tuple or slice, both integer/boolean or list of
            integers/booleans parameter is allowed
        .. note::

            When using tuple of integers as a parameter from previous note, the
            lengths of parameter tuple and index tuple (slice) must equal
        """
        return self._digital_out

    @property
    def analog_out(self) -> _GroupList[int]:
        """DAC output values

        :return: analog output values

        Usage (if one prefers function API, see
        :func:`set_analog_out<das.DAS.set_analog_out>`):

        >>> d.analog_out[1]  # Get single analog output value
        0
        >>> d.analog_out[2] = 1024  # Set value of the third analog output
        >>> d.analog_out[0:4]  # Get a slice of analog output pins
        [0, 0, 1024, 0]
        >>> d.analog_out[3:6] = 2233  # Set a slice of analog output pins
        >>> d.analog_out[1,2,3,4,5,6,7]  # Get a list of analog output pins
        [0, 1024, 2233, 2233, 2233, 0, 0]
        >>> d.analog_out[6,7] = [1000, 4000] # Set a list of analog output pins
        >>> d.analog_out[:]  # Get all analog output pins
        [0, 1024, 2233, 2233, 2233, 1000, 4000, 100]

        .. note::

            In order to set values or read the whole list, [:] must be used at
            the end.
        .. note::

            When setting a tuple or slice, both integer or list of integers
            parameter is allowed
        .. note::

            When using tuple of integers as a parameter from previous note, the
            lengths of parameter tuple and index tuple (slice) must equal
        """
        return self._analog_out

    @property
    def digital_pot(self) -> _GroupList[int]:
        """Digital potentiometers' values

        :return: digital potentiometers' values

        Usage (if one prefers function API, see
        :func:`set_digital_pot<das.DAS.set_digital_pot>`):
        >>> d.digital_pot[0]  # first parameter [0] is chip select
        >>> d.digital_pot[1]  # first parameter [0] is chip select---Get value of first potentiometer
        >>> d.digital_pot[1,2,0]  # Get a list of potentiometer value--first parameter [0] is chip select
        >>> d.digital_pot[[1,0]] = 135 # Chip select is 1 set value on second potentiometer
        >>> d.digital_pot[[3,1,3,4]] = 124 # Chip select is 3 set value 1,3,4 potentiometer
       

        .. note::

            In order to set values or read the whole list, [:] must be used at
            the end.
        .. note::

            When setting a tuple or slice, both integer or list of integers
            parameter is allowed
        .. note::

            When using tuple of integers as a parameter from previous note, the
            lengths of parameter tuple and index tuple (slice) must equal
        """
        return self._digital_pot

    @property
    def duty_cycle_out(self) -> int:
        """Output pwm duty-cycle value

        :return: duty-cycle output value

        Usage (if one prefers function API, see
        :func:`set_duty_cycle_out<das.DAS.set_duty_cycle_out>`):

        >>> d.duty_cycle_out  # Read both output pwm duty-cycles
        0
        >>> d.duty_cycle_out = 10  # Set duty-cycle of the first pwm output
        >>> d.duty_cycle_out
        10
        """
        return self.get_duty_cycle_out()

    @duty_cycle_out.setter
    def duty_cycle_out(self, value: int) -> None:
        """Set duty-cycle output value

        :param value: Desired duty-cycle output value
        """
        self.set_duty_cycle_out(value)

    @property
    def frequency_out(self) -> int:
        """Output frequency values

        :return: frequency output value

        Usage (if one prefers function API, see
        :func:`set_frequency_out<das.DAS.set_frequency_out>`):

        >>> d.frequency_out  # Read both output pwm duty-cycles
        0
        >>> d.frequency_out = 10  # Set duty-cycle of the first pwm output
        >>> d.frequency_out
        10
        """
        return self.get_frequency_out()

    @frequency_out.setter
    def frequency_out(self, value: int) -> None:
        """Set frequency output value

        :param value: Desired duty-cycle output value
        """
        self.set_frequency_out(value)

    @property
    def digital_in(self) -> _GroupList[bool]:
        """Fetch digital input states

        :return: digital input states

        Usage (if one prefers function API, see
        :func:`get_digital_in<das.DAS.set_digital_in>`):

        >>> d.digital_in[:]  # Read all digital inputs
        [False, False, False, False, False, False, False, True, False, False,
        False, True, False, False, True, False, False, False, False, False,
        False, False, False, False]
        >>> d.digital_in[7]  # Read single digital input
        True
        >>> d.digital_in[6:12]  # Read a slice of digital inputs
        [False, True, False, False, False, True]
        >>> d.digital_in[1,2,3]  # Read a tuple of digital inputs
        [False, False, False]
        """
        return self._digital_in
    
    @property
    def read_adc(self) -> _GroupList[float]:
        """Fetch digital input states
        """
        return self._read_adc
    @read_adc.getter
    def read_adc(self):
        
        return self._get_request(
            {ATTR_GROUP: GROUP_READ_ADC, ATTR_MODE: MODE_GET})
    
    @property
    def box_version(self) -> _GroupList[float]:
        """Fetch digital input states
        """
        return self._box_version
    @box_version.getter
    def box_version(self):
        
        return self._get_request(
            {ATTR_GROUP: GROUP_BOX_VERSION, ATTR_MODE: MODE_GET})
        
    @property
    def read_pwm(self) -> _GroupList[Dict[str, int]]:
        """Fetch pwm input state

        :return: pwm input values - {'f': int, 'd': int}

        Usage (if one prefers function API, see
        :func:`get_pwm_out<das.DAS.set_pwm_out>`):

        >>> d.read_pwm[:]  # Read input pwm signals
        [{'f': 2500, 'd': 50}, {'f': 2500, 'd': 50}]
        >>> d.read_pwm[0]['f']  # Read only input pwm signal frequency - for duty-cycle just replace f with d
        2500
        """
        #self._read_pwm[0] = self._get_pwm_in(0)
        #self._read_pwm[1] = self._get_pwm_in(1)
        return self._read_pwm
    @property
    def set_pwm1(self) -> None:
        """Set pwm1 frequency,duty-cycle 
        >>  d.set_pwm1 = (200,30) # first parameter(200) frequency second parameter(30) duty-cycle
        """
        return self._set_pwm1

    @property
    def set_pwm2(self) -> None:
        """Set pwm2 frequency,duty-cycle 

        >> d.set_pwm2 = (200,30) # first parameter(200) frequency second parameter(30) duty-cycle
        """
        return self.set_pwm2
    
    def get_main(self) -> bool:
        """Get main relay state

        :return: main switch state
        :rtype: bool

        Usage: see :func:`set_main<das.DAS.set_main>`
        """
        return self._get_request({ATTR_GROUP: GROUP_MAIN, ATTR_MODE: MODE_GET})

    def set_main(self, state: bool) -> None:
        """Set main relay on/off

        :param state: desired state of main relay
        :type state: bool
        :rtype: None

        Usage:

        >>> d.get_main()  # Read main relay state
        False
        >>> d.set_main(True)  # Set main relay state
        >>> d.get_main()
        True

        .. note::

            ``1/0`` or True ``True/False`` notation can be used.
        """
        self._request(
            {ATTR_GROUP: GROUP_MAIN, ATTR_MODE: MODE_SET, ATTR_VALUE: bool(state)}
        )

    def get_digital_out(
        self, index: Union[int, tuple, slice] = slice(None)
    ) -> Union[List[bool], bool]:
        """Get digital output states

        :return: digital output states

        Usage: see :func:`set_digital_out<das.DAS.set_digital_out>`
        """
        return self._digital_out[index]

    def set_digital_out(
        self, index: Union[int, tuple, slice], value: Union[bool, List[bool]]
    ) -> None:
        """Set digital output states

        :param index: single index or group of indexes
        :param value: single value or group of values

        Usage:

        >>> d.get_digital_out(1)  # Get single digital output state
        False
        >>> d.set_digital_out(1, True)  # Set second digital output state
        >>> d.get_digital_out(slice(0,4))   # Get a slice of digital output states
        [False, True, False, False]
        >>> d.set_digital_out((0,2,5,4,6), 1)  # Set multiple digital outputs to same state
        >>> d.get_digital_out()  # Get all digital output states
        [True, True, True, False, True, True, True, False]
        >>> d.set_digital_out(slice(0,5), False)  # Set slice of relays to same state
        >>> d.get_digital_out()
        [False, False, False, False, False, True, True, False]
        >>> d.set_digital_out(slice(None), 0)  # Set all relays to same state
        >>> d.get_digital_out()
        [False, False, False, False, False, False, False, False]
        >>> d.set_digital_out((1,2,3), [True, False, True])  # Set multiple digital outputs to different states
        >>> d.get_digital_out((1,2,3))
        [True, False, True]

        .. note::

            ``1/0`` or True ``True/False`` notation can be used.
        """
        self._digital_out[index] = value

    def get_analog_out(
        self, index: Union[int, tuple, slice] = slice(None)
    ) -> Union[List[int], int]:
        """DAC output values

        :return: analog output values

        Usage: see :func:`set_analog_out<das.DAS.set_analog_out>`
        """
        return self._analog_out[index]

    def set_analog_out(
        self, index: Union[int, tuple, slice], value: Union[List[int], int]
    ) -> None:
        """DAC output values

        Usage:

        >>> d.get_analog_out(1)  # Get single analog output value
        0
        >>> d.set_analog_out(2, 1024)  # Set value of the third analog output
        >>> d.get_analog_out(slice(0,4))  # Get a slice of analog output pins
        [0, 0, 1024, 0]
        >>> d.set_analog_out(slice(3,6), 2233)  # Set a slice of analog output pins
        >>> d.get_analog_out((1,2,3,4,5,6,7))  # Get a tuple of analog output pins
        [0, 1024, 2233, 2233, 2233, 0, 0]
        >>> d.set_analog_out((6,7), [1000, 4000]) # Set a tuple of analog output pins
        >>> d.get_analog_out()  # Get all analog output pins
        [0, 1024, 2233, 2233, 2233, 1000, 4000]
        """
        self._analog_out[index] = value

    def get_digital_pot(
        self,index: Union[int, tuple, slice] = slice(None)
    ) -> Union[List[int], int]:
        """Digital potentiometers' values

        :return: digital potentiometers' values

        Usage: see :func:`set_digital_pot<das.DAS.set_digital_pot>`
        """
        return self._digital_pot[index]

    def set_digital_pot(
        self, index: Union[int, tuple, slice], value: Union[List[int], int]
    ) -> None:
        """DAC output values

        Usage:
        >>> d.digital_pot[0]  # first parameter [0] is chip select
        >>> d.digital_pot[1]  # first parameter [0] is chip select---Get value of first potentiometer
        >>> d.digital_pot[1,2,0]  # Get a list of potentiometer value--first parameter [0] is chip select
        >>> d.digital_pot[[0,1]] = 135 # Chip select is 0 set value on second potentiometer
        >>> d.digital_pot[[3,1,3,4]] = 124 # Chip select is 3 set value 1,3,4 potentiometer
        """
        self._digital_pot[index] = value

    def get_duty_cycle_out(self) -> int:
        """Get output pwm duty-cycle value

        :return: duty-cycle output value

        Usage: see :func:`set_duty_cycle_out<das.DAS.set_duty_cycle_out>`
        """
        return self._get_request(
            {ATTR_GROUP: GROUP_DUTY_CYCLE_OUT, ATTR_MODE: MODE_GET}
        )

    def set_duty_cycle_out(self, value: int) -> None:
        """Set duty-cycle output value

        :param value: Desired duty-cycle output value

        Usage:

        >>> d.get_duty_cycle_out()  # Read both output pwm duty-cycles
        0
        >>> d.set_duty_cycle_out(10)  # Set duty-cycle of the first pwm output
        >>> d.get_duty_cycle_out()
        10
        """
        self._request(
            {ATTR_GROUP: GROUP_DUTY_CYCLE_OUT, ATTR_MODE: MODE_SET, ATTR_VALUE: value}
        )
    @set_pwm1.getter
    def set_pwm1(self) -> int:
        """ Get frequency and duty-cycle
        >> d.set_pwm1 # request for get frequency and duty cycle
        >> return [200,30] # return in list [frequency, duty-cycle]
        >> d.set_pwm1[0] # request for get frequency
        >> return 200 # return int frequency
        >> d.set_pwm1[1] # request for get duty-cycle
        >> return 30 # return int duty-cycle
        """
        return self._get_request(
            {ATTR_GROUP: GROUP_PWM_SET_1, ATTR_MODE: MODE_GET,}
        )
    @set_pwm1.setter
    def set_pwm1(self, value) -> None:
        """Set set_pwm1 frequency,duty-cycle 
        >>  d.set_pwm1 = (200,30) # first parameter(200) frequency second parameter(30) duty-cycle
        """
        frequency ,duty_cycle = value
        self._request(
            {ATTR_GROUP: GROUP_PWM_SET_1, ATTR_MODE: MODE_SET, ATTR_VALUE: [frequency,duty_cycle]}
        )
    @set_pwm2.getter
    def set_pwm2(self) -> int:
        """Get frequency and duty-cycle
        
        >> d.set_pwm2 # request for get frequency and duty cycle
        >> return [200,30] # return in list [frequency, duty-cycle]
        >> d.set_pwm2[0] # request for get frequency
        >> return 200 # return int frequency
        >> d.set_pwm2[1] # request for get duty-cycle
        >> return 30 # return int duty-cycle
        """
        return self._get_request(
            {ATTR_GROUP: GROUP_PWM_SET_2, ATTR_MODE: MODE_GET,}
        )
    @set_pwm2.setter
    def set_pwm2(self, value) -> None:
        """Set pwm1 frequency,duty_cycle 
        >>  d.set_pwm2 = (200,30) # first parameter(200) frequency second parameter(30) duty-cycle
        """
        frequency ,duty_cycle = value
        self._request(
            {ATTR_GROUP: GROUP_PWM_SET_2, ATTR_MODE: MODE_SET, ATTR_VALUE: [frequency,duty_cycle]}
        )
        
    
    def get_frequency_out(self) -> int:
        """Get output frequency value

        :return: frequency output value

        Usage: see :func:`set_frequency_out<das.DAS.set_frequency_out>`
        """
        return self._get_request({ATTR_GROUP: GROUP_FREQUENCY_OUT, ATTR_MODE: MODE_GET})

    def set_frequency_out(self, value: int) -> None:
        """Set duty-cycle output value

        :param value: Desired frequency output value

        Usage:

        >>> d.get_frequency_out()  # Read both output pwm duty-cycles
        0
        >>> d.set_frequency_out(10)  # Set duty-cycle of the first pwm output
        >>> d.get_frequency_out()
        10
        """
        self._request(
            {ATTR_GROUP: GROUP_FREQUENCY_OUT, ATTR_MODE: MODE_SET, ATTR_VALUE: value}
        )

    @property
    def set_voltage(self) -> float:
        """Output frequency values

        :return: frequency output value

        Usage (if one prefers function API, see
        :func:`set_frequency_out<das.DAS.set_frequency_out>`):

        >>> d.set_voltage # Read both output pwm duty-cycles
        0
        >>> d.set_voltage = (1,4)  # Set output, value
        >>> d.set_voltage
        10
        """
        return self._get_voltage()

    @set_voltage.setter
    def set_voltage(self, parameters: float) -> None:
        """Set frequency output value

        :param value: Desired duty-cycle output value
        """
        output,value = parameters
        self._request(
            {ATTR_GROUP: GROUP_SET_VOLTAGE, ATTR_MODE: MODE_SET, ATTR_VALUE: [output,value]}
        )
        
    @set_voltage.getter
    def set_voltage(self) -> float:
        """Get output voltage value

        :return: voltage output value

        Usage: see :func:`set_voltage<das.DAS.set_voltage>`
        """
        return self._get_request({ATTR_GROUP: GROUP_SET_VOLTAGE, ATTR_MODE: MODE_GET})
   
    def get_digital_in(
        self, index: Union[int, tuple, slice] = slice(None)
    ) -> Union[List[bool], bool]:
        """Get digital input states

        :param index: list/slice of indexes or single index
        :return: digital input states

        Usage:

        >>> d.get_digital_in()  # Read all digital inputs
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        >>> d.get_digital_in(7)  # Read single digital input
        1
        >>> d.get_digital_in(slice(6,12))  # Read a slice of digital inputs
        [0, 1, 0, 0, 0, 1]
        >>> d.get_digital_in((1,2,3))  # Read a tuple of digital inputs
        [0, 0, 0]
        """
        return self._digital_in[index]
    
    

    def get_pwm_in(
        self, index: Union[int, tuple, slice] = slice(None)
    ) -> List[Dict[str, int]]:
        """Get pwm input state

        :param index: list/slice of indexes or single index
        :return: pwm input values

        Usage:

        >>> d.get_pwm_in()  # Read input pwm signals
        [{'f': 2500, 'd': 50}, {'f': 2500, 'd': 50}]
        >>> d.get_pwm_in(0)['f']  # Read only input pwm signal frequency - for duty-cycle just replace f with d
        2500
        """
        return self._pwm_in[index]

    ########################################
    def reset(self) -> None:
        """Resets digital appliance simulator"""
        self.main = self.MAIN_DEFAULT
        self.duty_cycle_out = self.DUTY_CYCLE_OUT_DEFAULT
        self.frequency_out = self.FREQUENCY_OUT_DEFAULT
        self.digital_out[:] = [self.DIGITAL_OUT_DEFAULT] * DIGITAL_OUT_CNT
        self.analog_out[:] = [self.ANALOG_OUT_DEFAULT] * ANALOG_OUT_CNT

    def _get_digital_out(self, item):
        return self._get_request(
            {ATTR_GROUP: GROUP_DIGITAL_OUT, ATTR_MODE: MODE_GET, ATTR_VALUE: item}
        )

    def _set_digital_out(self, item, value):
        self._request(
            {
                ATTR_GROUP: GROUP_DIGITAL_OUT,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: [item, [bool(i) for i in value]],
            }
        )
        return value

    def _get_analog_out(self, item):
        return self._get_request(
            {ATTR_GROUP: GROUP_ANALOG_OUT, ATTR_MODE: MODE_GET, ATTR_VALUE: item}
        )

    def _set_analog_out(self, item, value):
        self._request(
            {
                ATTR_GROUP: GROUP_ANALOG_OUT,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: [item, value],
            }
        )
        return value

    def _get_digital_pot(self, item):
        return self._get_request(
            {ATTR_GROUP: GROUP_DIGITAL_POT, ATTR_MODE: MODE_GET, ATTR_VALUE: item}
        )

    def _set_digital_pot(self,item, value):
        #number = [item[0]]* (len(item)-1)
        self._request(
            {
                ATTR_GROUP: GROUP_DIGITAL_POT,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: [item[0],item[1:len(item)], value],
            }
        )

    def _get_digital_in(self, item):
        return self._get_request(
            {ATTR_GROUP: GROUP_DIGITAL_IN, ATTR_MODE: MODE_GET, ATTR_VALUE: item}
        )
    
    def _get_pwm_in(self, item):
        return self._get_request(
            {ATTR_GROUP: GROUP_PWM_IN, ATTR_MODE: MODE_GET, ATTR_VALUE: item}
        )
    
        