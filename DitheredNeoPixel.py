from rp2pio import StateMachine
from adafruit_pioasm import Program
import struct

#TODO
# should this have any gamma correction built in?


_program = Program(
    """
.side_set 1 opt
.wrap_target
    pull block          side 0
    out y, 32           side 0      ; get count of NeoPixel bits

bitloop:
    pull ifempty        side 0      ; drive low
    out x 1             side 0 [5]
    jmp !x do_zero      side 1 [3]  ; drive high and branch depending on bit val
    jmp y--, bitloop    side 1 [4]  ; drive high for a one (long pulse)
    jmp end_sequence    side 0      ; sequence is over

do_zero:
    jmp y--, bitloop    side 0 [4]  ; drive low for a zero (short pulse)

end_sequence:
    pull block          side 0      ; get fresh delay value
    out y, 32           side 0      ; get delay count
wait_reset:
    jmp y--, wait_reset side 0      ; wait until delay elapses
.wrap
        """
)

class DitheredNeopixel:
    def __init__(self,pin, number, extra_bit_depth, order=None, bpp=3,):
        self.byte_count = bpp * number
        self.bit_count = self.byte_count * 8
        self.padding_count = -self.byte_count % 4
        self.bpp = bpp
        self.extra_bit_depth = extra_bit_depth
        
        self.pixels = number
        
        self.pix_sm = StateMachine(
            _program.assembled,
            auto_pull=False,
            first_sideset_pin=pin,
            out_shift_right=False,
            pull_threshold=32,
            frequency=12_800_000,
            **_program.pio_kwargs,
        )
        
        # backwards, so that dma byteswap corrects it!
        header = struct.pack(">L", self.bit_count - 1)
        trailer = b"\0" * self.padding_count + struct.pack(">L", 3840)

        self.buf = bytearray((8+self.padding_count+self.byte_count)*self.extra_bit_depth)
        
        offset = 0
        for i in range(self.extra_bit_depth):
            for j in range(4):
                self.buf[offset+j] = header[j]
            for j in range(self.padding_count+4):
                self.buf[offset+self.byte_count+4+j] = trailer[j] # may need to take padding into account here? no padding is part of the trailer
            offset = offset+self.byte_count+8+self.padding_count 
       
    def __len__(self):
        return self.pixels
    
    def __repr__(self):
        pass
        #non-trivial -- see below
        
        
    def __getitem__(self):
        #hmm, this is actually a bit tricky -- do we store the un-split values (which would take a chunk of RAM)? Maybe not worth it
        pass
      
    #this isn't quite right. The shifts should be the log of the bit depth? maybe.
    #maybe the ceiling of the log?
    def __setitem__(self, number, colour):
        for i in range(self.bpp):
        #find closest 8 bit value
            error = 0
            for byte in range(self.extra_bit_depth):
                val = (colour[i] + error) >> self.extra_bit_depth

                self.buf[(self.byte_count+self.padding_count+8)*byte + 4 + number*3 + i] = val # possibly need to include padding?
                error = (colour[i]+error) - (val << self.extra_bit_depth)
        
    def start(self):
        self.pix_sm.background_write(loop=memoryview(self.buf).cast("L"), swap=True)
        
    def max_val(self):
        pass
        #return the maximum value so that you can map to it.
