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
  image_url: string | null;
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

type ListingSearchResult = {
  id: string;
  title: string;
  source_url: string;
  display_url: string | null;
  snippet: string | null;
  monthly_rent: number;
  currency_code: string;
  price_label: string;
  image_url: string | null;
  source_name: string;
  provider: string;
  rank: number;
};

const CURRENCY_OPTIONS = ["USD", "CAD", "GBP", "EUR", "AUD", "NZD"] as const;
const USD_RATES: Record<string, number> = {
  USD: 1,
  CAD: 1.37,
  GBP: 0.79,
  EUR: 0.92,
  AUD: 1.52,
  NZD: 1.65,
};
const COUNTRY_DEFAULT_CURRENCY: Record<string, string> = {
  "United States": "USD",
  Canada: "CAD",
  "United Kingdom": "GBP",
  Ireland: "EUR",
  France: "EUR",
  Germany: "EUR",
  Spain: "EUR",
  Italy: "EUR",
  Australia: "AUD",
  "New Zealand": "NZD",
};

function convertCurrency(value: number, fromCurrency: string, toCurrency: string) {
  const fromRate = USD_RATES[fromCurrency] ?? 1;
  const toRate = USD_RATES[toCurrency] ?? 1;
  return (value / fromRate) * toRate;
}

function currency(value: number | null | undefined, currencyCode = "USD") {
  if (value == null) return "Not enough data";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

function convertedCurrency(value: number | null | undefined, fromCurrency: string, toCurrency: string) {
  if (value == null) return "Not enough data";
  return currency(convertCurrency(value, fromCurrency, toCurrency), toCurrency);
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
  const [keyword, setKeyword] = useState("");
  const [budget, setBudget] = useState("");
  const [displayCurrency, setDisplayCurrency] = useState("USD");
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
  const [listingSearchResults, setListingSearchResults] = useState<ListingSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [schoolsLoading, setSchoolsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [notice, setNotice] = useState("Search a school to begin.");
  const resultsRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    function moveGlow(event: PointerEvent) {
      document.documentElement.style.setProperty("--cursor-x", `${event.clientX}px`);
      document.documentElement.style.setProperty("--cursor-y", `${event.clientY}px`);
    }

    window.addEventListener("pointermove", moveGlow, { passive: true });
    return () => window.removeEventListener("pointermove", moveGlow);
  }, []);

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

  function syncCurrencyForSchool(school: SchoolOption | null) {
    const nextCurrency = school?.country ? COUNTRY_DEFAULT_CURRENCY[school.country] : null;
    if (nextCurrency) {
      setDisplayCurrency(nextCurrency);
    }
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
    setListingSearchResults([]);
    window.setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 60);

    try {
      const params = new URLSearchParams({
        school_name: searchSchool,
        max_distance_miles: String(maxDistance),
        min_scam_safety: "70",
        limit: "8",
      });
      if (keyword.trim().length >= 2) {
        params.set("q", keyword.trim());
      }
      if (budget.trim().length > 0) {
        params.set("max_rent", budget.trim());
      }
      const [marketSettled, recSettled, leadsSettled, searchSettled] = await Promise.allSettled([
        api<MarketSummary>(`/api/v1/market/summary?school_name=${encodeURIComponent(searchSchool)}`),
        api<Recommendation[]>(`/api/v1/listings/recommendations?${params}`),
        api<HousingLead[]>(
          `/api/v1/housing-leads/nearby?school_name=${encodeURIComponent(searchSchool)}&radius_meters=3500&limit=20`,
        ),
        api<ListingSearchResult[]>(
          `/api/v1/listing-search/nearby?school_name=${encodeURIComponent(searchSchool)}&limit=8`,
        ),
      ]);

      const marketResult = marketSettled.status === "fulfilled" ? marketSettled.value : null;
      const recResult = recSettled.status === "fulfilled" ? recSettled.value : [];
      const leadsResult = leadsSettled.status === "fulfilled" ? leadsSettled.value : [];
      const searchResult = searchSettled.status === "fulfilled" ? searchSettled.value : [];

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
      setListingSearchResults(searchResult);
      setSelectedIds(recResult.slice(0, 2).map((item) => item.listing.id));
      setNotice(
        recResult.length > 0
          ? `${recResult.length} strong options found near ${marketResult?.school_name ?? searchSchool}.`
          : searchResult.length > 0
            ? `${searchResult.length} real external listing links found near ${marketResult?.school_name ?? searchSchool}.`
          : leadsResult.length > 0
            ? `${leadsResult.length} real nearby housing options found from public map data.`
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
          max_rent: budget.trim().length > 0 ? Number(budget) : null,
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

  const averageRentValue = hasSearched
    ? convertedCurrency(market?.average_rent, market?.currency_code ?? "USD", displayCurrency)
    : "Search first";
  const safeListingsValue = hasSearched
    ? market
      ? `${market.safe_listing_count}/${market.listing_count}`
      : "Loading"
    : "Search first";
  const averageDistanceValue = hasSearched
    ? market?.average_distance_miles
      ? `${market.average_distance_miles} mi`
      : "No data yet"
    : "Search first";

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
          <div className="nav-center">
            <a href="#results">Search</a>
            <a href="#sources">Sources</a>
            <a href="#contact">Contact</a>
          </div>
          <div className="nav-pill">
            <ShieldCheck size={16} />
            Get in Touch
          </div>
        </nav>

        <div className="hero-grid">
          <div className="hero-copy">
            <div className="eyebrow">
              <Sparkles size={16} />
              Off-campus only | priced listings first
            </div>
            <h1>
              Powering smarter <span>off-campus</span> housing search.
            </h1>
            <p>
              Search nearby apartments by school, budget, distance, price, and source quality.
              Dorms stay out; price-bearing rental links move to the top.
            </p>
          </div>

          <div className="workspace-panel">
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
                      syncCurrencyForSchool(school);
                      setSchools([]);
                      void runSearch(school.name);
                    }}
                  >
                    <span>
                      <strong>{school.name}</strong>
                      <small>{school.acronym} | {school.city}, {school.state}</small>
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
                  <input
                    value={keyword}
                    onChange={(event) => setKeyword(event.target.value)}
                    placeholder="Optional: studio, furnished, pet friendly..."
                  />
                </label>
                <label>
                  Budget
                  <input
                    type="number"
                    min="0"
                    value={budget}
                    onChange={(event) => setBudget(event.target.value)}
                    placeholder="Optional max rent"
                  />
                </label>
              </div>

              <div className="field-row">
                <label>
                  Display currency
                  <select value={displayCurrency} onChange={(event) => setDisplayCurrency(event.target.value)}>
                    {CURRENCY_OPTIONS.map((option) => (
                      <option value={option} key={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Student email for saves
                  <input
                    value={studentEmail}
                    onChange={(event) => setStudentEmail(event.target.value)}
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

              <button className="primary-action" onClick={() => void runSearch(schoolQuery)}>
                {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
                Search apartments
              </button>
              <p className="notice">{notice}</p>
              <SourceStatus sources={dataSources} />
            </div>

            <div className="preview-panel">
              <div className="preview-topline">
                <span>Live workspace</span>
                <strong>{hasSearched ? selectedSchool : "Ready"}</strong>
              </div>
              <div className="preview-stats">
                <StatCard icon={<TrendingUp />} label="Average rent" value={averageRentValue} />
                <StatCard icon={<ShieldCheck />} label="Safe listings" value={safeListingsValue} />
                <StatCard icon={<MapPin />} label="Avg. distance" value={averageDistanceValue} />
              </div>
              <div className="preview-result">
                <small>{listingSearchResults.length > 0 ? "Priced listings" : "Listing status"}</small>
                <strong>
                  {listingSearchResults.length > 0
                    ? `${listingSearchResults.length} priced links found`
                    : hasSearched
                      ? "Connect keys for priced listings"
                      : "Search to load results"}
                </strong>
                <p>
                  {hasSearched
                    ? "Only price-bearing listings appear as listing cards. Map leads stay as location context."
                    : "Search a school and CampusRent will rank priced listings when a listing API is configured."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className={`dashboard ${loading ? "is-refreshing" : ""}`} ref={resultsRef} id="results">
        <div className="stats-grid">
          <StatCard icon={<TrendingUp />} label="Average rent" value={averageRentValue} />
          <StatCard icon={<ShieldCheck />} label="Safe listings" value={safeListingsValue} />
          <StatCard icon={<MapPin />} label="Avg. distance" value={averageDistanceValue} />
        </div>

        {market && <div className="market-note">{market.budget_hint}</div>}

        <div className="section-header">
          <div>
            <span className="eyebrow compact">
              <SlidersHorizontal size={15} />
              Ranked results
            </span>
            <h2>{recommendations.length > 0 ? "Recommended apartments" : "Nearby housing options"}</h2>
          </div>
          <button className="secondary-action" onClick={() => void compareSelected()} disabled={selectedIds.length < 2}>
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
              <ListingImage src={item.listing.image_url} title={item.listing.title} />
              <div className="card-topline">
                <span>{item.listing.bedrooms ?? "?"} bd | {item.listing.bathrooms ?? "?"} ba</span>
                <strong>{item.campus_rent_score}</strong>
              </div>
              <h3>{item.listing.title}</h3>
              <p>{item.listing.address ?? `${item.listing.city}, ${item.listing.state}`}</p>
              <ListingContact listing={item.listing} />
              <div className="price-row">
                <span>{convertedCurrency(item.listing.monthly_rent, item.listing.currency_code, displayCurrency)}</span>
                <small>{item.distance_miles} mi | safety {item.scam_safety_score}</small>
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
          {recommendations.length === 0 &&
            listingSearchResults.map((result, index) => (
              <ListingSearchResultCard result={result} index={index} displayCurrency={displayCurrency} key={result.id} />
            ))}
        </div>

        {recommendations.length === 0 && listingSearchResults.length === 0 && housingLeads.length > 0 && (
          <div className="market-note">
            <strong>Map context is live, but priced listing cards need a listing API key.</strong>
            <span>
              CampusRent found nearby off-campus apartment buildings on the map. To import real price-bearing cards with images and source links,
              add a RentCast or SerpAPI key; until then, open a trusted rental search below.
            </span>
            <TrustedSearchLinks school={selectedSchoolMeta} query={selectedSchool} />
          </div>
        )}

        {recommendations.length > 0 && housingLeads.length > 0 && (
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

        {!loading && recommendations.length === 0 && listingSearchResults.length === 0 && housingLeads.length === 0 && (
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

function ListingSearchResultCard({
  result,
  index,
  displayCurrency,
}: {
  result: ListingSearchResult;
  index: number;
  displayCurrency: string;
}) {
  return (
    <article className="listing-card search-result-card" style={{ animationDelay: `${index * 50}ms` }}>
      <ListingImage src={result.image_url} title={result.title} />
      <div className="card-topline">
        <span>{result.source_name}</span>
        <strong>{result.rank}</strong>
      </div>
      <h3>{result.title}</h3>
      <p>{result.snippet ?? "Open the source page to review price, availability, photos, and contact information."}</p>
      <div className="contact-strip">
        <span>{result.display_url ?? result.provider}</span>
        <a href={result.source_url} target="_blank" rel="noreferrer">
          View listing
        </a>
      </div>
      <div className="price-row">
        <span>{convertedCurrency(result.monthly_rent, result.currency_code, displayCurrency)}</span>
        <small>source showed {result.price_label}</small>
      </div>
      <div className="card-actions">
        <a href={result.source_url} target="_blank" rel="noreferrer">
          <ExternalLink size={16} />
          Open source
        </a>
      </div>
    </article>
  );
}

function ListingImage({ src, title }: { src: string | null; title: string }) {
  return (
    <div className={`listing-image ${src ? "" : "is-empty"}`}>
      {src ? <img src={src} alt={`${title} preview`} loading="lazy" /> : <span>No source image</span>}
    </div>
  );
}

function HousingLeadCard({ lead, index }: { lead: HousingLead; index: number }) {
  return (
    <article className="listing-card lead-result-card" style={{ animationDelay: `${index * 50}ms` }}>
      <div className="card-topline">
        <span>Verified map source</span>
        <strong>{Math.max(72, 94 - index)}</strong>
      </div>
      <h3>{lead.name}</h3>
      <p>{lead.address ?? "Exact address not listed by the public map source."}</p>
      <div className="contact-strip">
        <span>{lead.website ? "Website available" : "Contact details may be on the source page"}</span>
        {lead.website ? (
          <a href={lead.website} target="_blank" rel="noreferrer">
            Open site
          </a>
        ) : (
          <a href={lead.source_url} target="_blank" rel="noreferrer">
            Open source
          </a>
        )}
      </div>
      <div className="price-row">
        <span>Price check needed</span>
        <small>{lead.source_name}</small>
      </div>
      <div className="card-actions">
        {lead.phone && <a href={`tel:${lead.phone}`}>Call</a>}
        {lead.email && <a href={`mailto:${lead.email}`}>Email</a>}
        {lead.website && (
          <a href={lead.website} target="_blank" rel="noreferrer">
            Website
          </a>
        )}
        <a href={lead.source_url} target="_blank" rel="noreferrer">
          <ExternalLink size={16} />
          Source
        </a>
      </div>
    </article>
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
  const mapOpenUrl =
    schoolPoint
      ? `https://www.openstreetmap.org/#map=14/${schoolPoint.lat}/${schoolPoint.lng}`
      : `https://www.openstreetmap.org/#map=14/${allPoints[0].lat}/${allPoints[0].lng}`;

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
        <a className="map-open-link" href={mapOpenUrl} target="_blank" rel="noreferrer">
          Open interactive map
        </a>
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
            title={`${point.title} | ${point.rent} | score ${point.score}`}
            aria-label={`${point.title}, ${point.rent}`}
          >
            <span>{index + 1}</span>
          </a>
        ))}
        {leadPoints.map((point) => (
          <a
            key={point.id}
            className="map-pin lead-pin"
            style={position(point.lat, point.lng)}
            href={point.url}
            target="_blank"
            rel="noreferrer"
            title={`${point.title} | housing lead`}
            aria-label={point.title}
          >
            <span />
          </a>
        ))}
      </div>
    </section>
  );
}
