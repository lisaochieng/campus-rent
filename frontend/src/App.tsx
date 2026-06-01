import {
  BadgeCheck,
  Building2,
  ExternalLink,
  Heart,
  Loader2,
  MapPin,
  PlugZap,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type SchoolOption = {
  id: string;
  name: string;
  city: string;
  state: string;
  country: string;
  latitude: string;
  longitude: string;
  acronym: string;
};

type MarketSummary = {
  school_name: string;
  city: string;
  state: string;
  latitude: string;
  longitude: string;
  listing_count: number;
  safe_listing_count: number;
  average_rent: number | null;
  currency_code: string | null;
  min_rent: number | null;
  max_rent: number | null;
  average_distance_miles: number | null;
  budget_hint: string;
};

type Listing = {
  id: string;
  source_url: string;
  title: string;
  address: string | null;
  city: string;
  state: string;
  country: string;
  latitude: string | null;
  longitude: string | null;
  monthly_rent: number;
  currency_code: string;
  bedrooms: string | null;
  bathrooms: string | null;
  square_feet: number | null;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
};

type Recommendation = {
  listing: Listing;
  distance_miles: number;
  scam_safety_score: number;
  campus_rent_score: number;
  affordability_score: number;
};

type Comparison = {
  listing: Listing;
  distance_miles: number;
  monthly_rent: number;
  rent_delta_from_budget: number | null;
  scam_safety_score: number;
  campus_rent_score: number;
  strengths: string[];
  tradeoffs: string[];
};

type DataSource = {
  key: string;
  source_name: string;
  description: string;
  requires_api_key: boolean;
  is_configured: boolean;
  coverage: string;
};

type HousingLead = {
  id: string;
  name: string;
  address: string | null;
  latitude: string;
  longitude: string;
  source_url: string;
  website: string | null;
  phone: string | null;
  email: string | null;
  source_name: string;
};

function currency(value: number | null | undefined, currencyCode = "USD") {
  if (value == null) return "Not enough data";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export default function App() {
  const [schoolQuery, setSchoolQuery] = useState("NYU");
  const [selectedSchool, setSelectedSchool] = useState("NYU");
  const [keyword, setKeyword] = useState("studio");
  const [budget, setBudget] = useState(3000);
  const [maxDistance, setMaxDistance] = useState(2);
  const [studentEmail, setStudentEmail] = useState("student@example.edu");
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [selectedSchoolMeta, setSelectedSchoolMeta] = useState<SchoolOption | null>(null);
  const [market, setMarket] = useState<MarketSummary | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [housingLeads, setHousingLeads] = useState<HousingLead[]>([]);
  const [loading, setLoading] = useState(false);
  const [schoolsLoading, setSchoolsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [notice, setNotice] = useState("Search a school to begin.");
  const resultsRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      if (schoolQuery.trim().length < 2) return;
      setSchoolsLoading(true);
      try {
        const results = await api<SchoolOption[]>(
          `/api/v1/schools/search?q=${encodeURIComponent(schoolQuery)}`,
        );
        setSchools(results);
      } catch {
        setSchools([]);
      } finally {
        setSchoolsLoading(false);
      }
    }, 250);

    return () => window.clearTimeout(timer);
  }, [schoolQuery]);

  useEffect(() => {
    void api<DataSource[]>("/api/v1/data-sources")
      .then(setDataSources)
      .catch(() => setDataSources([]));
  }, []);

  const selectedCards = useMemo(
    () => recommendations.filter((item) => selectedIds.includes(item.listing.id)),
    [recommendations, selectedIds],
  );

  function activeSchoolName(nextSchool?: string) {
    return (nextSchool ?? selectedSchoolMeta?.name ?? selectedSchool ?? schoolQuery).trim();
  }

  async function runSearch(nextSchool?: string) {
    const searchSchool = activeSchoolName(nextSchool);
    if (searchSchool.length < 2) {
      setNotice("Type a school name first.");
      return;
    }

    setSelectedSchool(searchSchool);
    setHasSearched(true);
    setLoading(true);
    setNotice("Finding apartments that fit your campus life...");
    setComparisons([]);
    setHousingLeads([]);
    window.setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 60);

    try {
      const params = new URLSearchParams({
        school_name: searchSchool,
        q: keyword,
        max_rent: String(budget),
        max_distance_miles: String(maxDistance),
        min_scam_safety: "70",
        limit: "8",
      });
      const [marketSettled, recSettled, leadsSettled] = await Promise.allSettled([
        api<MarketSummary>(`/api/v1/market/summary?school_name=${encodeURIComponent(searchSchool)}`),
        api<Recommendation[]>(`/api/v1/listings/recommendations?${params}`),
        api<HousingLead[]>(
          `/api/v1/housing-leads/nearby?school_name=${encodeURIComponent(searchSchool)}&radius_meters=3500&limit=20`,
        ),
      ]);

      const marketResult = marketSettled.status === "fulfilled" ? marketSettled.value : null;
      const recResult = recSettled.status === "fulfilled" ? recSettled.value : [];
      const leadsResult = leadsSettled.status === "fulfilled" ? leadsSettled.value : [];

      setMarket(
        marketResult ?? {
          school_name: searchSchool,
          city: selectedSchoolMeta?.city ?? "Unknown",
          state: selectedSchoolMeta?.state ?? "Unknown",
          latitude: selectedSchoolMeta?.latitude ?? "0",
          longitude: selectedSchoolMeta?.longitude ?? "0",
          listing_count: recResult.length,
          safe_listing_count: recResult.length,
          average_rent: null,
          currency_code: null,
          min_rent: null,
          max_rent: null,
          average_distance_miles: null,
          budget_hint: "Market data is still warming up for this school.",
        },
      );
      setRecommendations(recResult);
      setHousingLeads(leadsResult);
      setSelectedIds(recResult.slice(0, 2).map((item) => item.listing.id));
      setNotice(
        recResult.length > 0
          ? `${recResult.length} strong options found near ${marketResult?.school_name ?? searchSchool}.`
          : leadsResult.length > 0
            ? `No priced listings loaded yet, but ${leadsResult.length} real nearby housing leads are mapped.`
            : `No priced listings or housing leads loaded yet. Try a broader search or connect a rental listings API.`,
      );
    } catch {
      setNotice("I could not load that market yet. Try a broader school name or use one of the trusted source links below.");
    } finally {
      setLoading(false);
    }
  }

  async function saveListing(listingId: string) {
    try {
      await api("/api/v1/saved-listings", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          student_email: studentEmail,
          listing_id: listingId,
          note: "Saved from CampusRent dashboard",
        }),
      });
      setNotice("Saved to your shortlist.");
    } catch {
      setNotice("Already saved, or the email/listing needs a quick check.");
    }
  }

  async function compareSelected() {
    if (selectedIds.length < 2) {
      setNotice("Choose at least two listings to compare.");
      return;
    }
    setLoading(true);
    try {
      const result = await api<{ comparisons: Comparison[] }>("/api/v1/listings/compare", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          school_name: selectedSchool,
          listing_ids: selectedIds,
          max_rent: budget,
        }),
      });
      setComparisons(result.comparisons);
      setNotice("Comparison ready.");
    } finally {
      setLoading(false);
    }
  }

  function toggleListing(id: string) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : current.length < 5
          ? [...current, id]
          : current,
    );
  }

  return (
    <main>
      <section className="hero">
        <nav>
          <div className="brand">
            <span className="brand-mark">
              <Building2 size={22} />
            </span>
            <span>CampusRent</span>
          </div>
          <div className="nav-pill">
            <ShieldCheck size={16} />
            Scam-aware student housing
          </div>
        </nav>

        <div className="hero-grid">
          <div className="hero-copy">
            <div className="eyebrow">
              <Sparkles size={16} />
              Fast search, clean listings, smarter ranking
            </div>
            <h1>Find campus apartments with confidence.</h1>
            <p>
              Search by school, budget, distance, and trust signals. CampusRent blends
              recommendation scoring with saved listings and side-by-side comparison.
            </p>
          </div>

          <div className="search-panel">
            <label>
              School
              <div className="input-wrap">
                <Search size={18} />
                <input
                  value={schoolQuery}
                  onChange={(event) => setSchoolQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      void runSearch(schoolQuery);
                    }
                  }}
                  placeholder="NYU, Columbia, Berkeley..."
                />
                <button
                  className="inline-search"
                  type="button"
                  onClick={() => void runSearch(schoolQuery)}
                  aria-label="Search this school"
                >
                  <Search size={16} />
                </button>
              </div>
            </label>
            <div
              className={`school-suggestions ${schools.length > 0 || schoolsLoading ? "open" : ""}`}
              aria-hidden={schools.length === 0 && !schoolsLoading}
            >
              {schools.map((school) => (
                <button
                  className="school-option"
                  key={school.id}
                  onClick={() => {
                    setSelectedSchool(school.name);
                    setSchoolQuery(school.name);
                    setSelectedSchoolMeta(school);
                    setSchools([]);
                    void runSearch(school.name);
                  }}
                >
                  <span>
                    <strong>{school.name}</strong>
                    <small>{school.acronym} Â· {school.city}, {school.state}</small>
                  </span>
                  <em>Search</em>
                </button>
              ))}
              {schoolsLoading && (
                <div className="suggestion-loading">
                  <Loader2 className="spin" size={15} />
                  Searching global universities...
                </div>
              )}
            </div>

            <div className="field-row">
              <label>
                Keyword
                <input value={keyword} onChange={(event) => setKeyword(event.target.value)} />
              </label>
              <label>
                Budget
                <input
                  type="number"
                  value={budget}
                  onChange={(event) => setBudget(Number(event.target.value))}
                />
              </label>
            </div>

            <label>
              Max distance: {maxDistance} miles
              <input
                type="range"
                min="0.5"
                max="10"
                step="0.5"
                value={maxDistance}
                onChange={(event) => setMaxDistance(Number(event.target.value))}
              />
            </label>

            <label>
              Student email for saves
              <input
                value={studentEmail}
                onChange={(event) => setStudentEmail(event.target.value)}
              />
            </label>

            <button className="primary-action" onClick={() => void runSearch(schoolQuery)}>
              {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
              Search apartments
            </button>
            <p className="notice">{notice}</p>
            <SourceStatus sources={dataSources} />
          </div>
        </div>
      </section>

      <section className={`dashboard ${loading ? "is-refreshing" : ""}`} ref={resultsRef}>
        <div className="stats-grid">
          <StatCard icon={<TrendingUp />} label="Average rent" value={currency(market?.average_rent, market?.currency_code ?? "USD")} />
          <StatCard icon={<ShieldCheck />} label="Safe listings" value={market ? `${market.safe_listing_count}/${market.listing_count}` : "--"} />
          <StatCard icon={<MapPin />} label="Avg. distance" value={market?.average_distance_miles ? `${market.average_distance_miles} mi` : "--"} />
        </div>

        {market && <div className="market-note">{market.budget_hint}</div>}

        <div className="section-header">
          <div>
            <span className="eyebrow compact">
              <SlidersHorizontal size={15} />
              Ranked results
            </span>
            <h2>Recommended apartments</h2>
          </div>
          <button className="secondary-action" onClick={() => void compareSelected()}>
            <BadgeCheck size={17} />
            Compare selected ({selectedIds.length})
          </button>
        </div>

        {market && (
          <ListingMap recommendations={recommendations} housingLeads={housingLeads} school={selectedSchoolMeta} market={market} />
        )}

        {loading && recommendations.length === 0 && <ListingSkeletons />}

        <div className="listing-grid">
          {recommendations.map((item, index) => (
            <article className="listing-card" key={item.listing.id} style={{ animationDelay: `${index * 60}ms` }}>
              <div className="card-topline">
                <span>{item.listing.bedrooms ?? "?"} bd Â· {item.listing.bathrooms ?? "?"} ba</span>
                <strong>{item.campus_rent_score}</strong>
              </div>
              <h3>{item.listing.title}</h3>
              <p>{item.listing.address ?? `${item.listing.city}, ${item.listing.state}`}</p>
              <ListingContact listing={item.listing} />
              <div className="price-row">
                <span>{currency(item.listing.monthly_rent, item.listing.currency_code)}</span>
                <small>{item.distance_miles} mi Â· safety {item.scam_safety_score}</small>
              </div>
              <div className="card-actions">
                <button onClick={() => toggleListing(item.listing.id)} className={selectedIds.includes(item.listing.id) ? "selected" : ""}>
                  <BadgeCheck size={16} />
                  {selectedIds.includes(item.listing.id) ? "Selected" : "Select"}
                </button>
                <button onClick={() => void saveListing(item.listing.id)}>
                  <Heart size={16} />
                  Save
                </button>
                <a href={item.listing.source_url} target="_blank" rel="noreferrer">
                  <ExternalLink size={16} />
                  Source
                </a>
              </div>
            </article>
          ))}
        </div>

        {housingLeads.length > 0 && (
          <HousingLeadPanel leads={housingLeads} />
        )}

        {comparisons.length > 0 && (
          <section className="comparison-panel">
            <div className="section-header">
              <div>
                <span className="eyebrow compact">
                  <BadgeCheck size={15} />
                  Side by side
                </span>
                <h2>Comparison</h2>
              </div>
            </div>
            <div className="comparison-grid">
              {comparisons.map((item) => (
                <article key={item.listing.id} className="comparison-card">
                  <h3>{item.listing.title}</h3>
                  <div className="compare-metrics">
                    <span>{currency(item.monthly_rent, item.listing.currency_code)}</span>
                    <span>{item.distance_miles} mi</span>
                    <span>{item.campus_rent_score}/100</span>
                  </div>
                  <p><strong>Strengths:</strong> {item.strengths.join(", ")}</p>
                  <p><strong>Tradeoffs:</strong> {item.tradeoffs.join(", ")}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {!loading && recommendations.length === 0 && housingLeads.length === 0 && (
          <div className="empty-state">
            <Sparkles size={28} />
            <h2>{hasSearched ? "No imported listings for this search yet." : "Start with a school search."}</h2>
            <p>
              {hasSearched
                ? "CampusRent checked connected sources but did not find listings that match this school, keyword, budget, and distance yet. Try increasing distance, clearing the keyword, or opening a trusted source below."
                : "Try a school, then use the trusted source links below if CampusRent has not imported that market yet."}
            </p>
            <TrustedSearchLinks school={selectedSchoolMeta} query={selectedSchool} />
          </div>
        )}
      </section>
    </main>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="stat-card">
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function ListingContact({ listing }: { listing: Listing }) {
  const contactHref = listing.contact_email
    ? `mailto:${listing.contact_email}`
    : listing.contact_phone
      ? `tel:${listing.contact_phone}`
      : listing.source_url;
  const contactLabel = listing.contact_email
    ? "Email contact"
    : listing.contact_phone
      ? "Call contact"
      : "Contact via source";

  return (
    <div className="contact-strip">
      <span>{listing.contact_name ?? "Listing contact available on source"}</span>
      <a href={contactHref} target={contactHref.startsWith("http") ? "_blank" : undefined} rel="noreferrer">
        {contactLabel}
      </a>
    </div>
  );
}

function SourceStatus({ sources }: { sources: DataSource[] }) {
  const visibleSources = sources.filter((source) => !source.key.startsWith("demo-"));
  const realSources = visibleSources.filter((source) => source.requires_api_key);
  const configuredCount = realSources.filter((source) => source.is_configured).length;
  const publicCount = visibleSources.filter((source) => !source.requires_api_key && source.is_configured).length;
  const label =
    realSources.length === 0
      ? `${publicCount} public map/feed sources active`
      : configuredCount > 0
        ? `${configuredCount}/${realSources.length} priced listing APIs connected | ${publicCount} public map/feed sources active`
        : `Priced listing API not connected yet | ${publicCount} public map/feed sources active`;

  return (
    <div className="source-status">
      <PlugZap size={16} />
      <div>
        <strong>{label}</strong>
        <span>{visibleSources.map((source) => source.coverage).join(" | ") || "Loading source status..."}</span>
      </div>
    </div>
  );
}

function HousingLeadPanel({ leads }: { leads: HousingLead[] }) {
  return (
    <section className="lead-panel">
      <div className="section-header compact-header">
        <div>
          <span className="eyebrow compact">
            <MapPin size={15} />
            Real map leads
          </span>
          <h2>Nearby apartment buildings</h2>
        </div>
      </div>
      <div className="lead-grid">
        {leads.slice(0, 8).map((lead) => (
          <article className="lead-card" key={lead.id}>
            <h3>{lead.name}</h3>
            <p>{lead.address ?? "Address not listed in OpenStreetMap"}</p>
            <div className="lead-actions">
              {lead.website && (
                <a href={lead.website} target="_blank" rel="noreferrer">
                  Website
                </a>
              )}
              {lead.phone && <a href={`tel:${lead.phone}`}>Call</a>}
              {lead.email && <a href={`mailto:${lead.email}`}>Email</a>}
              <a href={lead.source_url} target="_blank" rel="noreferrer">
                Map source
              </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ListingSkeletons() {
  return (
    <div className="listing-grid skeleton-grid" aria-label="Loading apartments">
      {[0, 1, 2].map((item) => (
        <article className="listing-card skeleton-card" key={item}>
          <span />
          <strong />
          <p />
          <p />
          <div />
        </article>
      ))}
    </div>
  );
}

function TrustedSearchLinks({
  school,
  query,
}: {
  school: SchoolOption | null;
  query: string;
}) {
  const location = school ? `${school.city} ${school.state}` : query;
  const searchText = `${query} apartments near ${location}`;
  const links = [
    {
      label: "Google housing search",
      href: `https://www.google.com/search?q=${encodeURIComponent(searchText)}`,
    },
    {
      label: "Apartments.com",
      href: `https://www.apartments.com/search/?q=${encodeURIComponent(location)}`,
    },
    {
      label: "Zillow rentals",
      href: `https://www.zillow.com/homes/for_rent/${encodeURIComponent(location)}_rb/`,
    },
    {
      label: "OpenStreetMap area",
      href:
        school && school.latitude && school.longitude
          ? `https://www.openstreetmap.org/#map=14/${school.latitude}/${school.longitude}`
          : `https://www.openstreetmap.org/search?query=${encodeURIComponent(location)}`,
    },
    {
      label: "RentCast API setup",
      href: "https://developers.rentcast.io/reference/rental-listings-long-term",
    },
  ];

  return (
    <div className="trusted-links">
      {links.map((link) => (
        <a href={link.href} target="_blank" rel="noreferrer" key={link.label}>
          <ExternalLink size={15} />
          {link.label}
        </a>
      ))}
    </div>
  );
}

function ListingMap({
  recommendations,
  housingLeads,
  school,
  market,
}: {
  recommendations: Recommendation[];
  housingLeads: HousingLead[];
  school: SchoolOption | null;
  market: MarketSummary;
}) {
  const listingPoints = recommendations
    .map((item) => ({
      id: item.listing.id,
      title: item.listing.title,
      score: item.campus_rent_score,
      rent: currency(item.listing.monthly_rent, item.listing.currency_code),
      lat: Number(item.listing.latitude),
      lng: Number(item.listing.longitude),
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));
  const leadPoints = housingLeads
    .map((lead) => ({
      id: lead.id,
      title: lead.name,
      lat: Number(lead.latitude),
      lng: Number(lead.longitude),
      url: lead.source_url,
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));

  const schoolPoint =
    school && Number.isFinite(Number(school.latitude)) && Number.isFinite(Number(school.longitude))
      ? {
          title: school.name,
          lat: Number(school.latitude),
          lng: Number(school.longitude),
        }
      : Number.isFinite(Number(market.latitude)) && Number.isFinite(Number(market.longitude))
        ? {
            title: market.school_name,
            lat: Number(market.latitude),
            lng: Number(market.longitude),
          }
      : null;

  const allPoints = schoolPoint ? [...listingPoints, ...leadPoints, schoolPoint] : [...listingPoints, ...leadPoints];
  if (allPoints.length === 0) return null;

  const unmappedListings = recommendations.length - listingPoints.length;

  const lats = allPoints.map((point) => point.lat);
  const lngs = allPoints.map((point) => point.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const latSpan = maxLat - minLat || 0.01;
  const lngSpan = maxLng - minLng || 0.01;
  const bboxPadding = Math.max(latSpan, lngSpan, 0.02) * 0.45;
  const mapEmbedUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${minLng - bboxPadding}%2C${minLat - bboxPadding}%2C${maxLng + bboxPadding}%2C${maxLat + bboxPadding}&layer=mapnik`;

  function position(lat: number, lng: number) {
    return {
      left: `${8 + ((lng - minLng) / lngSpan) * 84}%`,
      top: `${92 - ((lat - minLat) / latSpan) * 84}%`,
    };
  }

  return (
    <section className="map-panel" aria-label="Listing locations">
      <div className="map-copy">
        <span className="eyebrow compact">
          <MapPin size={15} />
          Location view
        </span>
        <h3>
          {listingPoints.length > 0
            ? "Map the tradeoff between distance, score, and rent."
            : leadPoints.length > 0
              ? "Campus pinned with nearby real housing leads."
              : "Campus pinned. Listing coordinates will appear when sources provide them."}
        </h3>
        {unmappedListings > 0 && (
          <p>{unmappedListings} listing{unmappedListings === 1 ? "" : "s"} missing exact coordinates.</p>
        )}
      </div>
      <div className="map-canvas">
        <iframe
          src={mapEmbedUrl}
          title={`${market.school_name} area map`}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
        />
        {schoolPoint && (
          <div className="map-pin school-pin" style={position(schoolPoint.lat, schoolPoint.lng)}>
            <Building2 size={16} />
            <span>{school?.acronym ?? "Campus"}</span>
          </div>
        )}
        {listingPoints.map((point, index) => (
          <a
            key={point.id}
            className="map-pin listing-pin"
            style={position(point.lat, point.lng)}
            href={`https://www.openstreetmap.org/?mlat=${point.lat}&mlon=${point.lng}#map=15/${point.lat}/${point.lng}`}
            target="_blank"
            rel="noreferrer"
            title={`${point.title} Â· ${point.rent} Â· score ${point.score}`}
          >
            <span>{index + 1}</span>
          </a>
        ))}
        {leadPoints.map((point, index) => (
          <a
            key={point.id}
            className="map-pin lead-pin"
            style={position(point.lat, point.lng)}
            href={point.url}
            target="_blank"
            rel="noreferrer"
            title={`${point.title} Â· housing lead`}
          >
            <span>H{index + 1}</span>
          </a>
        ))}
      </div>
    </section>
  );
}
