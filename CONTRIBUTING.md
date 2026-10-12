# Contributing

Open an issue or pull request to add a CVPR 2026 paper, correct a link, or improve a translation.

- Check whether the paper is already listed. It may belong in more than one topic.
- Confirm its CVPR 2026 status against an official conference listing or the authors' project page.
- Keep the exact English title and use links supplied by the authors. Label unofficial implementations.
- Place it under the relevant topic. For a new topic, add a heading, a unique `cvpr-2026-topic-name` anchor, and a matching Contents link.

Use this format, omitting optional fields that do not apply:

```markdown
**Exact English Paper Title**

- Paper: https://example.org/paper
- Code: https://github.com/author/project
- Project: https://example.org/project
```

Use `Link not listed.` for an unavailable resource. Keep descriptions and labels in English.

Before submitting, run:

```sh
python3 scripts/validate.py
```

To compare paper titles and resource links with a downloaded upstream version:

```sh
python3 scripts/validate.py --upstream /path/to/CVPR2026-Papers-with-Code
```

These checks validate local navigation and source preservation; they do not check remote website availability. Record the source commit in [ATTRIBUTION.md](ATTRIBUTION.md) when incorporating upstream updates.
