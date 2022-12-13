from tester._clients.das import DAS  # Import DAS class






class A:
    
    def connect(self):    
        self.box = DAS('192.168.1.10')
        self.box.connect()
        print('box A connected',self.box.digital_out)



class B(A):
    def __init__(self):
        super().__init__()
    def check_input(self):
        print(self.box.digital_in)


b = B()
b.connect()

b.check_input()