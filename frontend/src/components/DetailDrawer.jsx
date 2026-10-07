import RiskBadge from "./RiskBadge";

function riskLevel(score) {
  if (score < 0.2) return "Low";
  if (score < 0.5) return "Medium";
  return "High";
}

export default function DetailDrawer({ item, data, loading, error, onClose }) {
  if (!item) return null;

  const displayName =
    item.category === "Book" ? `${item.publisher} — ${item.subject}` : item.subject || item.product_id;

  return (
    <>
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Details for ${displayName}`}>
        <button className="drawer__close" onClick={onClose} aria-label="Close">
          ✕
        </button>

        <p className="drawer__eyebrow">{item.branch}</p>
        <h2 className="drawer__title">{displayName}</h2>

        {loading && <p className="drawer__status">Reading the ledger…</p>}
        {error && <p className="drawer__status drawer__status--error">{error}</p>}

        {data && (
          <>
            <div className="drawer__risk">
              <span className="drawer__risk-number">{(data.risk_score * 100).toFixed(1)}%</span>
              <div>
                <RiskBadge level={riskLevel(data.risk_score)} />
                <p className="drawer__risk-caption">chance of stockout, next 7 days</p>
              </div>
            </div>

            <section className="drawer__section">
              <h3 className="drawer__section-title">Assessment</h3>
              <blockquote className="drawer__note">{data.explanation}</blockquote>
              {data.evidence_sources?.length > 0 && (
                <p className="drawer__sources">
                  Source{data.evidence_sources.length > 1 ? "s" : ""} referenced:{" "}
                  {data.evidence_sources.join(", ")}
                </p>
              )}
            </section>

            <section className="drawer__section">
              <h3 className="drawer__section-title">Recommended action</h3>
              <div className="chit">
                <span className="chit__stamp">DRAFT · APPROVAL REQUIRED</span>
                <dl className="chit__rows">
                  <div className="chit__row">
                    <dt>Quantity</dt>
                    <dd>{data.recommendation.recommended_qty} units</dd>
                  </div>
                  <div className="chit__row">
                    <dt>Source</dt>
                    <dd>
                      {data.recommendation.source_type === "transfer"
                        ? `Transfer from ${data.recommendation.source_branch}`
                        : "New supplier order"}
                    </dd>
                  </div>
                  <div className="chit__row">
                    <dt>Expected arrival</dt>
                    <dd>{data.recommendation.expected_arrival_days} day(s)</dd>
                  </div>
                  <div className="chit__row">
                    <dt>Priority</dt>
                    <dd>{data.recommendation.priority}</dd>
                  </div>
                </dl>
                <p className="chit__note">
                  This is a draft only. A branch manager must review and approve before any order is placed.
                </p>
              </div>
            </section>
          </>
        )}
      </aside>
    </>
  );
}
