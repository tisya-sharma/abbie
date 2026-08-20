# Datasheet fixtures

Text extracted from five published datasheets, one file per datasheet, pages separated by a form
feed. These are the parser's inputs, not the PDFs themselves: the PDFs run one to three megabytes
each and this repository is written to be public, so committing them would add fifty megabytes to
carry information the extracted text already holds.

The PDFs they came from are public at `https://proteininnovation.org/product/<slug>/`, which
redirects to the datasheet. Regenerating a fixture means fetching that URL and running
`packages.catalog.datasheet.extract_pages` over the bytes.

Chosen to cover the shapes the catalog actually contains rather than to be representative:

| Fixture | Why it is here |
|---|---|
| `cntn2-57` | The older template, five tested applications, all positive |
| `mntng1-4` | The newer template: `Species` rather than `Species reactivity`, `Storage Buffer` rather than `Storage buffer`, no `Amount` line, and a version stamp printed with a space |
| `gpc1-21` | A negative western blot row citing no publication, the `Not suitable for WB application` footnote, and a Community Data table underneath that must not be read as IPI's own |
| `nrxn1b-35` | Extracts as a label column followed by a value column, so half the Overview values come out empty. Fixture for the property that a datasheet like this yields no record |
| `ntn1-45` | Reactivity reads `human (mouse not tested)`, which no simple rule can tell apart from `human (mouse)`. Fixture for refusing to guess |
