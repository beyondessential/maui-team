<!--
PR title format: <type>(<scope>): <short description> (<linear-id>)
e.g. feat(reports): add diabetes line-list report (MAUI-1234)
Types: feature, feat, fix, hotfix, chore, refactor, docs
-->

## Summary

<!-- 1–3 bullets on what this changes and why. Reviewers should be able to grasp
the scope without opening the diff. -->

-

## Linear / spec

- Linear: MAUI-XXXX
- Spec: `<repo>/specs/<artefact-type>/<spec-name>.md` *(omit if no spec — fine for
  trivial fixes; see `.maui/knowledge/standards/sdd-conventions.md` for when a
  spec is required)*

## Test plan

<!-- What did you run? What should the reviewer run? Commands, screenshots,
links to CI runs. -->

- [ ]
- [ ]

## Risk and rollback

<!-- Anything reviewers should know about blast radius, dependent repos, or how
to roll back if this lands badly. Omit if there's nothing to flag. -->

## Checklist

- [ ] Title follows conventional commit format (Claude Code review will fix if
      vague)
- [ ] CI is green (or known failures noted above)
- [ ] Documentation updated (standards, runbooks, glossary, `AGENT.md` as
      applicable)
- [ ] Spec status updated if this implements or changes a spec
