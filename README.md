# Haoyu Xiong's website

Personal website served by GitHub Pages from this repository. The intended
canonical URL is **https://haoyux.ai/**; the existing address is
https://haoyu-x.github.io/.

## Existing deployment

- Repository: `haoyu-x/haoyu-x.github.io`.
- Static HTML, CSS, JavaScript, and assets at the repository root. There is no
  application build, site-generator configuration, or custom Actions workflow.
- The public deployment history identifies `main` and GitHub's built-in
  `pages build and deployment` workflow (`dynamic/pages/pages-build-deployment`).
  The inspected successful deployment used commit `8be8f1a`.
- Keep the existing **Deploy from a branch → main → / (root)** publishing source.
  The authenticated Pages settings could not be inspected from this environment;
  confirm these values in Settings without changing the publishing method.
- The root `CNAME` contains only `haoyux.ai`. Keep it in future deployments.
  This is a branch-published site, so the file is relevant. Custom Actions
  deployments ignore `CNAME`, but this migration does not introduce one.

There is one HTML page in this repository. `/simple-mobile/` is an existing
[separate project site](https://github.com/haoyu-x/simple-mobile), not a directory
to copy into this repository. GitHub Pages project sites without their own custom
domains inherit the account's user-site domain, so it should remain available at
`https://haoyux.ai/simple-mobile/`. Other project sites under this account can also
inherit the domain; check any additional published projects during the cutover.

## Verification notes

During the 2026-10-23 migration, the original live homepage matched this checkout's
original `index.html`. The custom domain was saved through GitHub's Pages settings,
which created a `CNAME` commit. Cloudflare's authoritative nameservers and Google's
resolver subsequently returned the expected DNS records, and valid HTTPS became
available for both the apex and `www` hosts.

Run the verifier below to check the current deployment. During a cutover, cached
responses can temporarily retain old HTTP redirect destinations or missing-page
responses even after fresh requests use the new HTTPS domain. A successful DNS
check alone does not verify HTTPS enforcement, deployed metadata, or every route.

The existing Simple Mobile HTML also references four resources that already
return `404`: `/simple-mobile/css/bootstrap.min.css`,
`/simple-mobile/css/app.css?v=20250608`, `/simple-mobile/js/app.js`, and
`/stylesheet.css`. Repair or remove those references in the separate project
repository; they are not caused by this domain migration. Its page and the
representative image assets used by the verifier currently return `200`.

## DNS records

The authoritative DNS is currently **Cloudflare**. Edit the `haoyux.ai` zone there
(changing DNS at a different registrar will have no effect while these nameservers
remain active). Use **DNS only**, with the Cloudflare proxy disabled, for these
records. TTL **Auto** is appropriate.

| Type | Name | Value |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `haoyu-x.github.io` |

Optional IPv6 records (add all four if using IPv6):

| Type | Name | Value |
| --- | --- | --- |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |

Replace conflicting web-hosting records for `@` and `www`. Preserve unrelated
email (`MX`), verification (`TXT`), and other service records. The DNS CNAME target
has no scheme or path; the repository's `CNAME` file has the custom hostname.
Do not use registrar forwarding, wildcard DNS, or a second website.

## Activate the existing site

1. Optionally verify ownership first under
   [account Settings → Pages](https://github.com/settings/pages): add `haoyux.ai`
   and publish GitHub's exact TXT challenge. The expected host is
   `_github-pages-challenge-haoyu-x.haoyux.ai`; GitHub supplies the unique value.
   Keep the verification record. This is separate from the repository's custom
   domain and does not redirect the existing site.
2. Prepare the DNS edits before starting the cutover. In
   [repository Settings → Pages](https://github.com/haoyu-x/haoyu-x.github.io/settings/pages),
   keep the current publishing source and set **Custom domain** to `haoyux.ai`
   (without `https://` or `www`). Save it, then immediately apply the DNS records
   above, following GitHub's documented order of custom-domain registration before
   DNS. **This activates a migration, not merely a preview:** the old address can
   start redirecting while DNS or the certificate is still being provisioned.
   Plan the steps together; zero interruption cannot be guaranteed on GitHub Pages.
3. Publish the prepared repository changes to `main` using the usual git workflow.
   Saving the custom domain in GitHub's UI may create a remote `CNAME` commit;
   reconcile that commit with the identical local file before pushing. Do not
   force-push or replace the deployment. Committing the local `CNAME` to the
   publishing branch can also activate the custom domain, so do not publish it
   long before the DNS cutover is ready.
4. Wait for GitHub's DNS check and certificate provisioning, then enable
   **Enforce HTTPS**. DNS propagation and HTTPS availability can take up to 24 hours.
   Check both `haoyux.ai` and `www.haoyux.ai`; a working apex certificate alone does
   not prove that the HTTPS `www` redirect works.
5. Run the verification command below. Do not call the migration complete until
   its checks pass. GitHub should serve the same site at the new domain and handle
   server-side redirects from the old hostname and `www`; there is no JavaScript,
   meta-refresh, custom redirect page, or new hosting service in these changes.

## Verification

From the repository root, with network access:

```sh
python3 scripts/verify-domain.py
```

This command checks real responses with normal TLS certificate validation:

- The apex home, CSS, JavaScript, images, favicon resources, robots.txt, and sitemap
  return `200`, including every local asset referenced by the homepage/manifest.
- `/simple-mobile/` and representative project assets still return `200`.
- HTTPS requests to the old hostname and `www` return **301**, with the exact
  canonical path and query in `Location`, including encoded and repeated values.
- HTTP upgrades end at the same HTTPS path and query with permanent redirects.
- The deployed homepage's canonical and social URLs, sitemap URLs, and robots.txt
  point to `https://haoyux.ai`.
- The example nonexistent paths `/xxx` and `/projects/demo?ref=test` redirect to
  the matching new-domain URLs, which still return a genuine `404`. A domain move
  preserves paths; it does not create pages or redirect missing pages to the home.

For individual checks:

```sh
curl -I 'https://haoyu-x.github.io/projects/demo?ref=test'
curl -I 'https://www.haoyux.ai/simple-mobile/?ref=test'
curl -IL 'https://haoyu-x.github.io/simple-mobile/?ref=test'
dig +noall +answer haoyux.ai A
dig +noall +answer haoyux.ai AAAA
dig +noall +answer www.haoyux.ai CNAME
```

Keep query strings quoted. Do not use `curl -k`, which hides certificate problems.
The verifier intentionally fails before the migration is activated.

## Search engines and ongoing maintenance

- The homepage has a self-referencing canonical, Open Graph URLs, and Twitter
  image URL on the new HTTPS domain. `/index.html` and tracking-query variants
  canonicalize to `/`. Existing relative asset paths and section navigation stay
  valid at the same URL paths.
- `sitemap.xml` lists the one HTML page owned by this repository. Add new canonical
  page URLs as pages are added; do not list assets, tracking variants, or fake paths.
  Give each future page its own canonical URL rather than copying the homepage's.
- In the **separate `simple-mobile` repository**, add a self-referencing canonical
  for `https://haoyux.ai/simple-mobile/` and review any absolute old-domain URLs
  and metadata. Its inspected live HTML has no canonical tag. This repository
  cannot set another project's HTML metadata; do not copy that project here.
- Verify both the old `https://haoyu-x.github.io/` URL-prefix property and the new
  domain/property in Google Search Console. Keep verification tokens/files in
  place. After redirects work, submit a **Change of Address** from the old property
  and submit `https://haoyux.ai/sitemap.xml` for the new one. Add the new domain to
  Bing Webmaster Tools if used, and update the existing GA4 web stream's website URL.
- Update profile/backlink URLs you control. Keep the repository, old address, and
  permanent redirects working indefinitely so old bookmarks and inbound links
  remain useful. Do not block the old host from crawling or request its removal.
- Google uses permanent redirects to consolidate signals and discover the new
  canonical domain. Rankings can fluctuate during recrawling; neither zero SEO
  fluctuation nor ranking for the literal old address can be guaranteed. The old
  address still takes visitors to the corresponding new URL once redirects work.

References: [GitHub custom-domain setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site),
[project-site inheritance](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages),
[GitHub HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https),
[Google site moves](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes),
[Search Console Change of Address](https://support.google.com/webmasters/answer/9370220).

## Credits

Based on [Andy Zeng's academic website](https://andyzeng.github.io/), inspired by
[Jon Barron's website](https://jonbarron.info/).
