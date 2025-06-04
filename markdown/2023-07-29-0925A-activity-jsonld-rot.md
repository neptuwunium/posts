---
title: json-ld is misused
short: it's not just fancy json.
date: 2023-07-28 9:25 AM
unlist: 1
---

ActivityStreams is a subset of JSON-LD, specifically the compacted form.

> This specification describes a JSON-based RFC7159 serialization syntax for the Activity Vocabulary that conforms to a subset of JSON-LD syntax constraints but does not require JSON-LD processing. While other serialization forms are possible, such alternatives are not discussed by this document[^assyntax].

> The serialized JSON form of an Activity Streams 2.0 document MUST be consistent with what would be produced by the standard JSON-LD 1.0 Processing Algorithms and JSON-LD-API Compaction Algorithm using, at least, the normative JSON-LD @context definition provided here[^asjsonld].

[^assyntax]: [https://www.w3.org/TR/activitystreams-core/#syntaxconventions](https://www.w3.org/TR/activitystreams-core/#syntaxconventions)
[^asjsonld]: [https://www.w3.org/TR/activitystreams-core/#jsonld](https://www.w3.org/TR/activitystreams-core/#jsonld0)

This essentially looks like fancy JSON with a schema attached to it.
But it's not... That `@context` is important, and **not** set in stone.

> For extensions, JSON-LD is used as the primary mechanism for defining and disambiguating extensions. Implementations that wish to fully support extensions SHOULD use JSON-LD mechanisms. 

> It is important to note that the JSON-LD Processing Algorithms, as currently defined, will silently ignore any property not defined in a JSON-LD @context. Implementations that publish Activity Streams 2.0 documents containing extension properties SHOULD provide a @context definition for all extensions[^asextensibility]. 

[^asextensibility]:[https://www.w3.org/TR/activitystreams-core/#extensibility](https://www.w3.org/TR/activitystreams-core/#extensibility)

While Activity vocabulary is set in stone and should not and will not ever change,
Extensions are not.

When sending an ActivityStreams message, you cannot rename, override or replace ActivityStreams predicates but this does not apply to extensions.

Given the following example:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
        "foo": "http://example.org/foo"
    }
  ],
  "@id": "https://example.org/example/note",
  "type": "Note",
  "content": "This is a simple note",
  "foo": 123
}
```

This is still a valid ActivityStreams message, but **you should avoid accessing `"foo"` directly.**

Why? Overlap and disambiguation.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
        "foo": "http://example.org/foo",
        "other_foo": "http://another.example.org/foo"
    }
  ],
  "@id": "https://example.org/example/note",
  "type": "Note",
  "content": "This is a simple note",
  "foo": 123,
  "other_foo": 456
}
```

Both `"foo"` and `"other_foo"` are `foo` terms. 
They can swap, or even be a different term entierly. It's implementation-defined.
This would still be a valid JSON-LD object and a valid Activity Object.

Then, there's also the use of IRIs.

```json
{   
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
        "ex": "http://example.org/",
        "foo": "ex:foo",
        "ex2": "http://another.example.org/"
    }
  ],
  "@id": "https://example.org/example/note",
  "type": "Note",
  "content": "This is a simple note",
  "foo": 123,
  "ex2:foo": 456
}
```

This one is more set-in-stone, however you should still verify that the namespace is actually what you expect. 
However now everyone is forced to use "ex2:foo" if we were to include this extension (much like we're currently forced to use the short IRI `"vcard:location"`)

JSON-LD algorithms would transform all three objects, essentially into:

```json
{
  "@id": "https://example.org/example/note",
  "https://www.w3.org/ns/activitystreams/type": "Note",
  "https://www.w3.org/ns/activitystreams/content": "This is a simple note",
  "http://example.org/foo": 123,
  "http://another.example.org/foo": 456
}
```

and

```json
{
  "@id": "https://example.org/example/note",
  "as:type": "Note",
  "as:content": "This is a simple note",
  "ex:foo": 123,
  "ex2:foo": 456
}
```

You would then just access it via either it's shortened IRI, or it's full URI-- disambiguating the result.
This is very important because as ActivityPub is getting more popular, and more third-party extensions are introduced by Litepub, Misskey, and others.

I found this out when I was looking into adding `schema:license` and `schema:description` into ActivityStreams' `Image` type. 
To provide a means to define a copyright SPDX and/or author citation, while also allowing for descriptive text[^ap-descriptive-text].
As it stands right now, i'm using `schema:license` and `schema:description` directly into the object;
now knowing that every implementation will have to blindly check that short IRI.

[^ap-descriptive-text]: ActivityPub nor ActivityStreams defines how descriptive text is supposed to be federated. Right now most implementations store in the `"name"` field of the Image which I find a bit silly especially since new implementations might be unaware of this quirk and potentially use a giant blob of text as the filename if they make the same assumption I did.

The only social-network-style ActivityPub implementation that I've found that implements proper JSON-LD parsing is GoToSocial,
which very effectively utilizes Go's struct tags to map JSON-LD URIs to struct fields.

I do understand that processing JSON-LD at all is way more computationally heavy than JSON by itself, 
but if you're going to introduce JSON-LD extension contexts **please** create a json-ld spec file[^its-just-xml].

You can federate anything over ActivityStreams, even new Activity types if you wanted-- as long as you properly define them.
Support for them in other platforms might not ever exist, though.

[^its-just-xml]: Compacted JSON-LD is essentially just JSON with XMLNS DTD features.
