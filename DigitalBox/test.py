def connect(self):
    """
    Connect to serial port and read device version.
    """

    VERSION = ""

    try:
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port = self.comport
        self.ser.timeout = 1
        self.ser.setDTR(False)
        self.ser.setRTS(False)
        self.ser.open()

        sleep(3)

        # Request version
        self.ser.write(CHECK_VERSION.encode())
        sleep(SEND_TIME)

        raw = self.ser.readline()

        print(f"RAW RX: {raw!r}")

        VERSION = raw.decode(errors="replace").strip()

        print(f"VERSION: {VERSION}")

        # Print any remaining data in buffer
        remaining = self.ser.read_all()
        if remaining:
            print(f"REMAINING RX: {remaining!r}")

    except Exception:
        print("Device disconnected")

        x = datetime.datetime.now()
        dateAndTime = x.strftime("%c")

        with open("check_error.txt", "a") as f:
            f.write(f"{errorNumber}{dateAndTime}{errorNumber}\n")
            f.write(traceback.format_exc())
            f.write(f"{errorNumber * 2}\n")

        try:
            if hasattr(self, "ser") and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    return VERSION