---
title: bitpacking cheat codes
short: up up down down left right left right b a start
date: 2024-09-27 12:39 AM
headers: math
---

**Note:** This document has a lot of code snippets and may be unsuitable for screen readers.

A little while ago we were talking to someone about cheat-codes in old games 
and how they're very often stored as numbers, but how would you implement something like that?

In theory you need to figure out how many key states you need to track, because the "up-up-down-down" code is extremely iconic I'll be using that for this post but really anything can work.

So the code goes something like `up up down down left right left right b a`. 
That's 6 states, let's add in a seventh for a reset state.

```py
from enum import Enum


class BUTTON_STATE(Enum):
  BUTTON_RESET = 0
  BUTTON_UP = 1
  BUTTON_RIGHT = 2
  BUTTON_DOWN = 3
  BUTTON_LEFT = 4
  BUTTON_B = 5
  BUTTON_A = 6
```

That's the easy part. Now we need to figure out how many bits one state would take. Fortunately it's a simple equation.

## $$\lfloor \frac{n}{\lceil \log_2(S) \rceil} \rfloor$$

Where `n` is the number of total bits available for storage, and `S` is the number of states.

```py
from math import ceil, log2


# we have 6 states + a reset value
NUMBER_OF_STATES = 7

# we are storing in a 32-bit integer
BITS = 32

# the number of bits required to safely store the state value, which can be no more than 7
STORAGE_WIDTH = ceil(log2(NUMBER_OF_STATES))

# the maximum number of states we can store in our number
MAX_SEQUENCE = BITS // STORAGE_WIDTH

print(f'{STORAGE_WIDTH} bits can fit {MAX_SEQUENCE} times in {BITS} bits')
# 3 bits can fit 10 times in 32 bits
```

This means that we can store 10 states in a 32-bit number!

Okay, now we need to calculate a magic check value.
We do this by shifting the bits to the right by *3* (since that's the bit width of all states), and do the same with an accompanying mask value.

```py
# test sequence value
seq = 0
# test mask value
mask = 0


def handle_seq(state):
    global seq, mask

    # shift sequence to the right by 3 bits, since that's all our states use.
    seq = seq << 3
    # apply the button state bits to the sequence
    seq |= state

    # repeat the same but with all bits set, so we can later check the appropriate amount of bits
    mask = mask << 3
    mask |= (1 << 3) - 1


# emulate button presses
handle_seq(BUTTON_STATE.BUTTON_UP.value)
handle_seq(BUTTON_STATE.BUTTON_UP.value)
handle_seq(BUTTON_STATE.BUTTON_DOWN.value)
handle_seq(BUTTON_STATE.BUTTON_DOWN.value)
handle_seq(BUTTON_STATE.BUTTON_LEFT.value)
handle_seq(BUTTON_STATE.BUTTON_RIGHT.value)
handle_seq(BUTTON_STATE.BUTTON_LEFT.value)
handle_seq(BUTTON_STATE.BUTTON_RIGHT.value)
handle_seq(BUTTON_STATE.BUTTON_B.value)
handle_seq(BUTTON_STATE.BUTTON_A.value)

print(f'the code sequence is {hex(seq)} and masked by {hex(mask)}')
# the code sequence is 0x96e28ae and masked by 0x3fffffff
```

So now we have our input code sequence and our bit test mask. Now all we have to do is replicate the code in some input event loop.

```py
egg_seq = 0

def handle_egg_button_press(state):
  global egg_seq

  # append the state bits to our sequence tracker for this easter egg (and restrict it to 64-bits)
  egg_seq = ((egg_seq << 3) | state) & 0xffffffffffffffff

  # if the last 30 bits do not match to our pre-calculated value, return early.
  if (egg_seq & 0x3fffffff) != 0x96e28ae:
    return
  
  # the secret has been found!

  # reset state so we can't accidentally trigger it again 
  egg_seq = 0

  # better trigger it :)
  trigger_egg_secret()
```

And that's all there's to it. Just a little bit (heh) of bit manipulation and bit packing.

This has a lot of advantages, such as: 

- Only really using 4 (or 8) bytes of memory
- Doesn't use recursion or any loops.
- We aren't pre-emptively checking if the input state is correct for this code, we simply only care for the correct sequence. This means we can check multiple cheat sequences in the same function. 
- A little harder to notice if somene is hunting through game source code for debug or cheat input sequences

In practice, a conventional controller will have about 16 states and a keyboard will have on average 105 states. This means a code can reasonably be 4 keyboard inputs long in a 32-bit number, or 8 controller inputs. However, in the year 2024 we can safely use 64-bit, which expectedly double the storage space compared to 32-bit. We're also only using basic bit manipulation, so we could use SIMD and expand this to 128-bits and 256-bits of storage (18/36 states for keyboard, 32/64 for controller). 256-bit numbers will work on x86-64 computers released in the last decade, assuming they have the AVX2 instruction set available.
