function displayName(item) {
  if (item.category === "Book") return `${item.publisher} — ${item.subject}`;
  return item.subject || item.product_id;
}

export default function ProductLedger({ items, onSelect, selectedId }) {
  if (items.length === 0) {
    return (
      <div className="ledger__empty">
        <p>No entries match your search.</p>
      </div>
    );
  }

  return (
    <table className="ledger">
      <thead>
        <tr>
          <th>Product</th>
          <th>Category</th>
          <th>Branch</th>
          <th aria-hidden="true"></th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => {
          const rowKey = `${item.product_id}__${item.branch}`;
          const isSelected = rowKey === selectedId;
          return (
            <tr
              key={rowKey}
              className={`ledger__row ${isSelected ? "ledger__row--selected" : ""}`}
              onClick={() => onSelect(item)}
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && onSelect(item)}
            >
              <td className="ledger__name">{displayName(item)}</td>
              <td className="ledger__category">{item.category}</td>
              <td>{item.branch}</td>
              <td className="ledger__arrow">→</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
