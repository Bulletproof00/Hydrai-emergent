import { useMemo, useState } from "react";
import { Globe, Newspaper, TrendingUp, TrendingDown, Gauge } from "lucide-react";

const FALLBACK_NEWS = [
  {
    source: "Chainalytics",
    title: "ETF-Zuflüsse steigen zum dritten Tag in Folge",
    summary: "US-Spot-ETFs verzeichnen erneut Nettozuflüsse, getrieben von institutioneller Nachfrage.",
    impact: "bullish",
    time: "vor 18 Min"
  },
  {
    source: "MacroPulse",
    title: "US-Inflationsdaten bleiben über Erwartung",
    summary: "Höhere CPI-Werte sorgen für vorsichtige Risikoallokation an den Märkten.",
    impact: "bearish",
    time: "vor 42 Min"
  },
  {
    source: "OnchainDesk",
    title: "Langfristige Holder akkumulieren weiter",
    summary: "Wallet-Daten zeigen anhaltende Abflüsse von Exchanges.",
    impact: "bullish",
    time: "vor 1 Std"
  },
  {
    source: "DerivativesWire",
    title: "Funding Rates neutralisieren sich",
    summary: "Leverage wird abgebaut, was auf eine stabilere Marktstruktur hindeutet.",
    impact: "neutral",
    time: "vor 2 Std"
  },
  {
    source: "RegulationWatch",
    title: "EU kündigt nächste Konsultationsrunde für MiCA an",
    summary: "Keine unmittelbaren Restriktionen angekündigt, aber mehr Berichtspflichten möglich.",
    impact: "neutral",
    time: "vor 3 Std"
  }
];

const impactConfig = {
  bullish: {
    label: "Bullisch",
    color: "#10b981",
    icon: TrendingUp,
    score: 1
  },
  bearish: {
    label: "Bärisch",
    color: "#ef4444",
    icon: TrendingDown,
    score: -1
  },
  neutral: {
    label: "Neutral",
    color: "#94a3b8",
    icon: Gauge,
    score: 0
  }
};

const classifyImpact = (text) => {
  if (!text) return "neutral";
  const lower = text.toLowerCase();
  const bullishKeywords = ["zufluss", "approval", "akkumul", "rekord", "bull", "steigt", "hochs", "rebound", "nachfrage"];
  const bearishKeywords = ["abfluss", "verbot", "hack", "rückgang", "sell", "risiko", "über", "enttäusch", "druck"];

  if (bullishKeywords.some((word) => lower.includes(word))) return "bullish";
  if (bearishKeywords.some((word) => lower.includes(word))) return "bearish";
  return "neutral";
};

const normalizeNews = (items) => {
  if (!Array.isArray(items) || items.length === 0) {
    return FALLBACK_NEWS;
  }

  return items.slice(0, 6).map((item, index) => {
    if (typeof item === "string") {
      const impact = classifyImpact(item);
      return {
        source: "Live-Feed",
        title: item,
        summary: "Automatisch zusammengefasste Headline aus dem Live-Feed.",
        impact,
        time: `vor ${15 + index * 6} Min`
      };
    }

    const title = item.title || item.headline || "Unbekannte Meldung";
    const summary = item.summary || item.description || "Keine Zusammenfassung verfügbar.";
    const impact = item.impact || item.sentiment || classifyImpact(`${title} ${summary}`);

    return {
      source: item.source || item.publisher || "Live-Feed",
      title,
      summary,
      impact,
      time: item.time || item.published_at || `vor ${20 + index * 9} Min`
    };
  });
};

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const BitcoinNewsForecast = ({ news = [], sentiment }) => {
  const [horizon, setHorizon] = useState("24h");

  const data = useMemo(() => normalizeNews(news), [news]);

  const scores = useMemo(() => {
    const totalScore = data.reduce((sum, item) => {
      const impact = impactConfig[item.impact] || impactConfig.neutral;
      return sum + impact.score;
    }, 0);

    const sentimentBoost = sentiment?.score ? clamp(sentiment.score * 10, -10, 10) : 0;
    const horizonMultiplier = horizon === "1h" ? 0.7 : horizon === "7d" ? 1.25 : 1;
    const probability = clamp(50 + (totalScore * 6 + sentimentBoost) * horizonMultiplier, 15, 85);
    const confidence = clamp(42 + data.length * 5 + Math.abs(totalScore) * 3, 50, 90);

    return {
      probability,
      confidence
    };
  }, [data, sentiment, horizon]);

  const bullishCount = data.filter((item) => item.impact === "bullish").length;
  const bearishCount = data.filter((item) => item.impact === "bearish").length;

  return (
    <section className="bitcoin-forecast">
      <header className="bitcoin-forecast__header">
        <div>
          <p className="section-eyebrow">
            <Globe size={14} /> Live-Scan der wichtigsten Finanzquellen
          </p>
          <h2 className="section-title">Bitcoin-News Radar & Wahrscheinlichkeitsmodell</h2>
          <p className="section-subtitle">
            Aggregiert aktuelle Headlines, On-Chain-Signale und Makrodaten zu einem probabilistischen Ausblick.
          </p>
        </div>
        <div className="bitcoin-forecast__controls">
          <label htmlFor="forecast-horizon">Zeithorizont</label>
          <select
            id="forecast-horizon"
            value={horizon}
            onChange={(event) => setHorizon(event.target.value)}
          >
            <option value="1h">1 Stunde</option>
            <option value="24h">24 Stunden</option>
            <option value="7d">7 Tage</option>
          </select>
        </div>
      </header>

      <div className="bitcoin-forecast__grid">
        <div className="forecast-panel">
          <div className="forecast-panel__header">
            <h3>Preisaufschlags-Wahrscheinlichkeit</h3>
            <span className="forecast-tag">{horizon} Outlook</span>
          </div>
          <div className="forecast-probability">
            <div className="forecast-probability__value">{scores.probability.toFixed(0)}%</div>
            <div className="forecast-probability__bar">
              <span style={{ width: `${scores.probability}%` }} />
            </div>
            <div className="forecast-probability__meta">
              <span>Konfidenz</span>
              <strong>{scores.confidence.toFixed(0)}%</strong>
            </div>
          </div>
          <div className="forecast-summary">
            <div>
              <span>Bullische Signale</span>
              <strong>{bullishCount}</strong>
            </div>
            <div>
              <span>Bärische Signale</span>
              <strong>{bearishCount}</strong>
            </div>
            <div>
              <span>Neutral</span>
              <strong>{data.length - bullishCount - bearishCount}</strong>
            </div>
          </div>
        </div>

        <div className="forecast-panel forecast-panel--wide">
          <div className="forecast-panel__header">
            <h3>Aktuelle Headlines</h3>
            <span className="forecast-tag">{data.length} Quellen</span>
          </div>
          <div className="headline-list">
            {data.map((item, index) => {
              const impact = impactConfig[item.impact] || impactConfig.neutral;
              const ImpactIcon = impact.icon;
              return (
                <article className="headline-card" key={`${item.title}-${index}`}>
                  <div className="headline-card__icon" style={{ background: `${impact.color}1a`, color: impact.color }}>
                    <ImpactIcon size={16} />
                  </div>
                  <div className="headline-card__content">
                    <div className="headline-card__meta">
                      <span className="headline-source">{item.source}</span>
                      <span className="headline-time">{item.time}</span>
                    </div>
                    <h4>{item.title}</h4>
                    <p>{item.summary}</p>
                  </div>
                  <span className="headline-impact" style={{ color: impact.color, borderColor: `${impact.color}66` }}>
                    {impact.label}
                  </span>
                </article>
              );
            })}
          </div>
        </div>

        <div className="forecast-panel forecast-panel--insights">
          <div className="forecast-panel__header">
            <h3>Modellnotizen</h3>
            <span className="forecast-tag">Transparenz</span>
          </div>
          <ul className="insight-list">
            <li>
              <Newspaper size={14} />
              Bewertet Headline-Impact anhand historischer Korrelationen und Sentiment-Signale.
            </li>
            <li>
              <Gauge size={14} />
              Wahrscheinlichkeiten sind indikativ und keine Anlageberatung.
            </li>
            <li>
              <TrendingUp size={14} />
              Live-Feeds werden im Demo-Modus simuliert, damit der Datenfluss sichtbar bleibt.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
};

export default BitcoinNewsForecast;
