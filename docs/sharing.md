# Sharing this project on GitHub

This folder is the repository root. It contains the runnable app, selected research originals, derived artifacts, provenance, examples and documentation. The surrounding private working directory is not needed. The suggested repository name is **`useless-speed`**.

## Prepare and publish

1. Install Git and Git LFS. Run `git lfs install --local` inside this repository before adding files.
2. Run `npm ci`, `npm test`, `npm run build` and `python tools/verify_snapshot.py`.
3. Review `git status --short`, the license notices and the files you intend to publish.
4. Create an empty GitHub repository named `useless-speed` under the account/organization you choose. Avoid generating a second README or license there.
5. Commit this folder and connect the new remote:

```sh
# If you are starting from an exported folder without .git, first run:
git init -b main
git lfs install --local
git add .
git commit -m "Publish Useless Speed app and research corpus"
git remote add origin YOUR_GITHUB_CLONE_URL
git push -u origin main
```

Use the real clone URL, not the placeholder. On a repo that already has a remote/commit history, use its normal contribution workflow instead of reinitializing it. The local project setup does not create a GitHub repository or choose its owner/visibility.

## Large files

`.gitattributes` configures LFS for original research files and heavy derived outputs. The app's compact data stays in regular Git, so it runs even in an LFS-skipping checkout. Git's text conversions are disabled for fingerprinted data to preserve byte hashes across operating systems.

GitHub blocks ordinary Git files over 100 MiB; some original research files exceed that limit. Do not remove the LFS rules and add those files as ordinary blobs. [GitHub large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

After staging, `git lfs ls-files` lists tracked LFS objects. Verify the first push finishes uploading those objects. A repository containing only pointer files on the server does not distribute the data. LFS storage/download allowances depend on the hosting plan, so check them before inviting many full-corpus downloads. [LFS billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)

GitHub's source ZIPs normally contain LFS pointers unless the repository's archive setting includes LFS objects. The README recommends cloning with Git LFS and provides commands for app-only and selective downloads. [Archive settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository)

## What the release includes

- All 223 selected successful catalog records, including 63 byte-identical duplicates.
- The offline catalog, checked timing subset, candidate pages, SQLite index, OCR, workbook cells and CSV exports.
- Public source URLs, hashes, timestamps, field schemas, discovery metadata and recorded failures.
- The app's address/stop supplements, prepared map layers and a route fixture.
- Source code and scripts needed to understand or reproduce the compilation.

It excludes local `.venv`, `node_modules`, runtime caches, logs, browser profiles, generated build/test folders, unrelated exploratory originals and captured website script bodies. Discovery metadata can reference unsuccessful or unselected source files that are not included; the successful selected catalog is the authoritative inclusion list.

Original code/documentation uses MIT. Source documents and derived agency records retain their original rights; [DATA_LICENSES.md](../DATA_LICENSES.md) explains the boundary. Keep the source URLs and document-level provenance when publishing a subset or a derivative dataset.

## Before announcing it

Clone the pushed repository into a fresh directory, fetch the LFS data you want, and repeat the README's quick start and snapshot check. Confirm the catalog opens and source-file links resolve. Add the real repository URL to citation/release metadata if desired, and link a hosted app only after that deployment has been verified.
