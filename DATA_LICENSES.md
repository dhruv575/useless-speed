# Data, attribution and licensing

The repository's MIT license applies to original Useless Speed code and documentation. It does **not** grant a new license over third-party source documents, observations, map data, styles, extracted text, or workbook contents. Derived exports retain the relevant source rights. No single uniform open-data license has been established for this entire compilation.

| Material | Origin and attribution | Reuse status / retained notices |
|---|---|---|
| Signal cards, CAD, engineering records and correspondence | SFMTA / San Francisco public-records archive; individual document URLs in the catalog | Publicly retrieved agency records; third-party authorship/rights can vary. No blanket relicensing asserted. |
| Environmental review and transportation appendices | SF Planning and document authors/consultants | Preserve report authors, revision/scenario and original source URL. Public availability alone is not a uniform reuse license. |
| Signal, speed-limit, lane, one-way, green-wave and stop-sign layers | SFMTA ArcGIS services | Preserve agency attribution and source/schema URLs; consult each layer's metadata and terms. |
| SF address directory | SF Enterprise Addressing System, DataSF dataset `3mea-di5p` | Preserve DataSF/agency attribution and dataset metadata. No resident-level data was collected for address search. |
| Place-name search index (`app/data/places.json`) | © OpenStreetMap contributors, retrieved through Overpass; query and timestamp in `app/data/places-provenance.json` | This OSM-derived database is available under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Retain attribution and applicable share-alike obligations; it is separate from the MIT-licensed code. |
| Traffic observations and CMP geometry | SFCTA dashboards and public API; some observations are described as INRIX-derived by the provider | Preserve SFCTA/provider attribution. We have not established a blanket license to redistribute or commercially reuse all provider-derived observations. Check the applicable source terms for your use. |
| Route fixture and returned route geometry | OSRM routing service / OpenStreetMap | Preserve OpenStreetMap attribution; public demo service terms are separate from data rights. |
| Basemap data | OpenFreeMap serving OpenStreetMap/OpenMapTiles data | Maintain the map's visible attribution and the source's applicable data terms. |
| Customized Positron map style | OpenFreeMap, OpenMapTiles, CartoDB Basemaps, Stamen and Paul Norman | Upstream notices are in `app/public/map-style-license.md` and `app/public/positron-license.md`; colors, label density and casing were modified. |
| Fonts, icons and libraries | DM Sans, Noto Sans, Lucide and npm/Python dependencies | Each retains its own license; see upstream packages and style notices. |

Source starting points:

- [San Francisco public records](https://sanfrancisco.nextrequest.com/documents)
- [SF Planning environmental review library](https://sfplanning.org/environmental-review-documents)
- [SFMTA traffic layers](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer)
- [DataSF address dataset](https://data.sf.gov/d/3mea-di5p)
- [SFCTA congestion dashboard](https://congestion.sfcta.org/) and [CMP dashboard](https://cmp.sfcta.org/)
- [OpenStreetMap copyright and license information](https://www.openstreetmap.org/copyright)
- [OpenFreeMap](https://openfreemap.org/) and [style source](https://github.com/hyperknot/openfreemap-styles)
- [OSRM demo usage policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server)

Keep source URLs, hashes, retrieval dates and page references in exports so downstream users can check the original evidence and terms. Cite Useless Speed for compilation/methods and the originating agencies/documents for the actual data. Public records may contain incidental names, agency account identifiers or correspondence; those are preserved source context, not targets for personal profiling.

If a rights holder or source maintainer identifies a problem, document the affected file/hash, preserve the provenance record, and adjust distribution as appropriate. The code can be reused independently of every research file.
