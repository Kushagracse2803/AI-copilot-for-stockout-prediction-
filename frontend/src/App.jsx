import { useEffect, useMemo, useState } from "react";
import Header from "./components/Header";
import ProductLedger from "./components/ProductLedger";
import DetailDrawer from "./components/DetailDrawer";
import { fetchProducts, fetchExplanation } from "./api";
import "./App.css";

export default function App() {
  const [products, setProducts] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");

  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((err) => setLoadError(err.message));
  }, []);

  const filtered = useMemo(() => {
    return products.filter((p) => {
      const matchesCategory = category === "All" || p.category === category;
      const haystack = `${p.product_id} ${p.branch} ${p.publisher} ${p.subject}`.toLowerCase();
      const matchesQuery = haystack.includes(query.toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [products, query, category]);

  function handleSelect(item) {
    setSelected(item);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);

    fetchExplanation(item.product_id, item.branch)
      .then(setDetail)
      .catch((err) => setDetailError(err.message))
      .finally(() => setDetailLoading(false));
  }

  const selectedId = selected ? `${selected.product_id}__${selected.branch}` : null;

  return (
    <div className="app">
      <Header
        query={query}
        onQueryChange={setQuery}
        category={category}
        onCategoryChange={setCategory}
        count={filtered.length}
      />

      <main className="app__main">
        {loadError && (
          <p className="app__error">
            Could not reach the API ({loadError}). Is the FastAPI server running on port 8000?
          </p>
        )}
        {!loadError && <ProductLedger items={filtered} onSelect={handleSelect} selectedId={selectedId} />}
      </main>

      <DetailDrawer
        item={selected}
        data={detail}
        loading={detailLoading}
        error={detailError}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
