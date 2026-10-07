const CATEGORIES = ["All", "Book", "Notebook", "Stationery"];

export default function Header({ query, onQueryChange, category, onCategoryChange, count }) {
  return (
    <header className="header">
      <div className="header__mark">
        <h1>Om Traders</h1>
        <p className="header__tagline">Stockout risk &amp; replenishment ledger</p>
      </div>

      <div className="header__controls">
        <input
          type="text"
          className="header__search"
          placeholder="Search a product or branch…"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
        />
        <div className="header__tabs" role="tablist" aria-label="Filter by category">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              role="tab"
              aria-selected={category === c}
              className={`header__tab ${category === c ? "header__tab--active" : ""}`}
              onClick={() => onCategoryChange(c)}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <p className="header__count">{count} entries in the ledger</p>
    </header>
  );
}
