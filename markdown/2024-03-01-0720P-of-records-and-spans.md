---
title: of records and spans
short: this is just me rambling about a csharp feature
date: 2024-03-01 07:20 PM
unlist: 1
---
<!--
SPDX-FileCopyrightText: 2026 Neptuwunium

SPDX-License-Identifier: EUPL-1.2
-->

This post is mostly just me speaking fondly of Spans and Records
with no real technical information besides how cool they are and their use cases.

This is not a guide, or tutorial, or a technical writeup.
Just good vibes about new language features.

Beware! It does get a bit rambly at times.

Anyway, let's go back a few years, to the year 2015...

## Spans

.NET 2015 just released, bringing along with it better control over the
.NET Garbage Collector and a little footnote that reads:

> .NET Core packages such as the immutable collections, SIMD APIs, and
> networking APIs such as those found in the System.Net.Http namespace
> are now available as open-source packages on GitHub.

.NET was moving to open source.

Fast forward another 3 years, it's now 2018.

An update to .NET Core is released, .NET Core 2.1, bringing with it four new
types that represent a whole new programming paradigm. Span, and Memory.

Span is unique in that it's a **reference struct.** Preventing it from moving
out of the stack.

### Wait, C# has a stack?

Yes! C# has several tiers of memory management, the stack exists in the smallest
area. This space always exist, and it's where variables end up.
Every time you do a `new AwesomeClass()` or `new string[]`, it makes this in
the heap and just stores a bit of info on where this is in the heap in the stack

### So how does this relate to Span?

When you create a span via `new Span<T>()` or read a memory segment via `(Span<T>) SomeArray`,
this value entirely lives in the stack and only in the stack. Meaning you cannot
store it in the heap.

### Isn't this a massive issue with OOP designs?

Not if you consider what Span is used for. Span allows you to quickly wrap and
manipulate structures and arrays without actually copying memory repeatedly.

Let's say I'm reading a small file, and I need to read the opening for a blog
summary. This line is expected to be about... 40 characters long. What I can do
is read this line without actually allocating any heap memory using `stackalloc`
Turns out this is a massive speed improvement. Who guessed not allocating memory
is faster?

Memory is the functional equivalent of Span, except that it lives in the heap.
This means it has the luxury of granting a Span (without allocating more
memory!) and having access to all of the features, such as _Slicing._

### Slicing?

Slicing is taking a portion of an array, in such that you can manipulate and
move it around better. With memory and spans, it just makes a new struct with
the same data with some info to only work on that specific range.No data gets
copied, whereas making a slice in Arrays requires building (and copying!) a
whole second array.

Using Span (when allocated using `stackalloc`) and Memory buffers (if you need
to allocate in to the heap), you can easily avoid repeatedly allocating and
duplicating data which in turn results in major speed gains.

### But what about Native Interopability?

You know how, if you want to pass an array into a native library method,
you would have to do something like:

```cs
[DllImport] void NativeCall(byte* buffer, int size);

byte[] myArray = new byte[100];
unsafe {
    fixed(byte* pointer = &myArray[0]) {
        NativeCall(pointer, myArray.Length);
    }
}
```

Well, using Memory this is not only safer, but also a way nicer API.

```cs
Memory<byte> myArray = new byte[100];
using var memoryHandle = myArray.Pin();
NativeCall(memoryHandle.Pointer, myArray.Length);
```

Pretty cool huh?

## Records

We're still in 2018, so let's move forwards a bit to 2020.
.NET 5 just released, marking the start of a new era.
Dotnet is finally, fully and properly cross platform.
With it comes a new kind of structure, `record` and `record struct`

### How is this different from `class` and `struct`, aren't they just the same?

Functionally, there are a few different expectations with records that are
quite important. _Records prefer to be immutable._
It also introduced a few concepts such as
**primary constructors and init-only properties**

Let's imagine I have a class called `MeowAction` that is something like:

```cs
public class MeowAction {
    public float Volume { get; set; }
    public Subject MeowedAt { get; set; }
    public DateTimeOffset MeowedAtTime { get; set; } = DateTimeOffset.UtcNow;

    public MeowAction(float vol, Subject subject) {
        Volume = vol;
        MeowedAt = subject;
    }
}

// later...

new MeowAction(Volume.Loud, RandomStranger());
```

Simple meow-keeping class for a meow auditing system. However, as a data holding class
it's still doing some amount of predictable copying (which can be an issue!)

What if I told you this is the exact use case for Records?

Let's reimplement it as a record:

```cs
public record MeowAction(float Volume, Subject MeowedAt) {
    public DateTimeOffset MeowedAtTime { get; init; } = DateTimeOffset.UtcNow;
}
```

Way smaller, right?

### Wait, init? What happened to set?

With primary constructors in records, the default behavior is to mark properties as init-only.
As such, if you want to have the parameters as a normal get, set pair you would have to
something like:

```cs
public record MeowAction(float Volume, Subject MeowedAt) {
    public float Volume { get; set; } = Volume;
    public DateTimeOffset MeowedAtTime { get; init; } = DateTimeOffset.UtcNow;
}
```

### Could this not be integrated into a class?

As it turns out, it has.
There's nothing stopping you from using `class` instead of `record`

So why all this fanfare then? Because that's the beauty of records.
It shows that C# is willing to adopt new designs, such as...

### It has deconstructors for the primary constructor arguments

```cs
var action = new MeowAction(Volume.Loud, RandomStranger());
var (volume, subject) = action;
```

### It generates ToString

```cs
var action = new MeowAction(Volume.Loud, RandomStranger());
action.ToString();
// MeowAction { Volume = 85.0, MeowedAt = Person { Name = "Ada" }, MeowedAtTime = 2165-06-02 }
```

### It generates GetHashCode

```cs
var action = new MeowAction(Volume.Loud, RandomStranger());
action.GetHashCode(); // HashCode.Combine(Volume, MeowedAt, MeowedAtTime);
```

### It clones

```cs
var action = new MeowAction(Volume.Loud, RandomStranger());
var mutated = action with { Volume = Volume.VeryLoud };
```

### Cloning?!

Remember when I mentioned that Records prefer to be immutable?
This is how you get around that.

Any property marked with `set` or `init` can be mutated using curly braces like this.
The `with` keyword just happens to copy every value that isn't specified.

## Conclusion

This was a quite long but non-exhaustive fanfare for Span, Memory, and Records.
It's an exciting time to develop in C#, the language progressively is introducing
new featuers (such as nullability checks!) that improve code quality, speed and
overall encourage a more reliable way of programming.

I encourage you to consider weaving stackalloc, Span, Memory, Records,
and Struct Records into your projects targeting .NET 7 and newer.

Hint: A good use case of the `record` keyword are options or settings objects.

### Secret afterword

Did you know that you can have a `readonly record struct` which enforces complete immutability?

### Special Thanks

Thanks to [scarletquasar](https://github.com/scarletquasar) for some corrections.
