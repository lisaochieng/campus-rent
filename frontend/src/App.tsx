import {
  BadgeCheck,
  Building2,
  Heart,
  Loader2,
  MapPin,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type SchoolOption = {
  id: string;
  name: string;
  city: string;
  state: string;
  acronym: string;
};

type MarketSummary = {
  school_name: string;
  city: string;
  state: string;
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
  title: string;
  address: string | null;
  city: string;
  state: string;
  country: string;
  monthly_rent: number;
  currency_code: string;
  bedrooms: string | null;
  bathrooms: string | null;
  square_feet: number | null;
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
  const [market, setMarket] = useState<MarketSummary | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("Search a school to begin.");

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      if (schoolQuery.trim().length < 2) return;
      try {
        const results = await api<SchoolOption[]>(
          `/api/v1/schools/search?q=${encodeURIComponent(schoolQuery)}`,
        );
        setSchools(results);
      } catch {
        setSchools([]);
      }
    }, 250);

    return () => window.clearTimeout(timer);
  }, [schoolQuery]);

  const selectedCards = useMemo(
    () => recommendations.filter((item) => selectedIds.includes(item.listing.id)),
    [recommendations, selectedIds],
  );

  async function runSearch(nextSchool = selectedSchool) {
    setLoading(true);
    setNotice("Finding apartments that fit your campus life...");
    setComparisons([]);
    try {
      const params = new URLSearchParams({
        school_name: nextSchool,
        q: keyword,
        max_rent: String(budget),
        max_distance_miles: String(maxDistance),
        min_scam_safety: "70",
        limit: "8",
      });
      const [marketResult, recResult] = await Promise.all([
        api<MarketSummary>(`/api/v1/market/summary?school_name=${encodeURIComponent(nextSchool)}`),
        api<Recommendation[]>(`/api/v1/listings/recommendations?${params}`),
      ]);
      setMarket(marketResult);
      setRecommendations(recResult);
      setSelectedIds(recResult.slice(0, 2).map((item) => item.listing.id));
      setNotice(`${recResult.length} strong options found near ${marketResult.school_name}.`);
    } catch {
      setNotice("I could not load that market yet. Try NYU, Columbia, or Berkeley.");
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
                  placeholder="NYU, Columbia, Berkeley..."
                />
              </div>
            </label>
            {schools.length > 0 && (
              <div className="school-suggestions">
                {schools.map((school) => (
                  <button
                    key={school.id}
                    onClick={() => {
                      setSelectedSchool(school.acronym);
                      setSchoolQuery(school.acronym);
                      void runSearch(school.acronym);
                    }}
                  >
                    <span>{school.name}</span>
                    <small>{school.acronym} · {school.city}, {school.state}</small>
                  </button>
                ))}
              </div>
            )}

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

            <button className="primary-action" onClick={() => void runSearch()}>
              {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
              Search apartments
            </button>
            <p className="notice">{notice}</p>
          </div>
        </div>
      </section>

      <section className="dashboard">
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

        <div className="listing-grid">
          {recommendations.map((item, index) => (
            <article className="listing-card" key={item.listing.id} style={{ animationDelay: `${index * 60}ms` }}>
              <div className="card-topline">
                <span>{item.listing.bedrooms ?? "?"} bd · {item.listing.bathrooms ?? "?"} ba</span>
                <strong>{item.campus_rent_score}</strong>
              </div>
              <h3>{item.listing.title}</h3>
              <p>{item.listing.address ?? `${item.listing.city}, ${item.listing.state}`}</p>
              <div className="price-row">
                <span>{currency(item.listing.monthly_rent, item.listing.currency_code)}</span>
                <small>{item.distance_miles} mi · safety {item.scam_safety_score}</small>
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
              </div>
            </article>
          ))}
        </div>

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

        {recommendations.length === 0 && (
          <div className="empty-state">
            <Sparkles size={28} />
            <h2>Start with a school search.</h2>
            <p>Try NYU, Columbia, or Berkeley using the search panel above.</p>
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
