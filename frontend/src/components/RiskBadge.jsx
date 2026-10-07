const LEVEL_STYLES = {
  Low: { color: "var(--risk-low)", label: "Low risk" },
  Medium: { color: "var(--risk-medium)", label: "Medium risk" },
  High: { color: "var(--risk-high)", label: "High risk" },
};

export default function RiskBadge({ level }) {
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.Low;
  return (
    <span className="risk-badge" style={{ "--badge-color": style.color }}>
      <span className="risk-badge__dot" />
      {style.label}
    </span>
  );
}
