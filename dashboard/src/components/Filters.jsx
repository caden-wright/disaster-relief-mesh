import { BANDS } from "../live.js";

export default function Filters({ filters, setFilters, meta, shown, total, onReset }) {
  const set = (key) => (e) =>
    setFilters((f) => ({ ...f, [key]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  const hps = meta?.help_points ?? [];
  const shelterName = (hp) => meta?.shelters?.[hp] || `Help Point ${hp}`;

  return (
    <div className="filters" role="search">
      <label>
        <span>Type</span>
        <select value={filters.type} onChange={set("type")}>
          <option value="all">All types</option>
          {["MEDICAL_URGENT", "RESOURCE_REQUEST", "CHECKIN"].map((t) => (
            <option key={t} value={t}>{BANDS[t].name}</option>
          ))}
        </select>
      </label>
      <label>
        <span>Shelter</span>
        <select value={filters.hp} onChange={set("hp")}>
          <option value="all">All shelters</option>
          {hps.map((hp) => (
            <option key={hp} value={String(hp)}>{shelterName(hp)}</option>
          ))}
        </select>
      </label>
      <label>
        <span>Status</span>
        <select value={filters.ack} onChange={set("ack")}>
          <option value="open">Not resolved</option>
          <option value="new">New</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
          <option value="all">Everything</option>
        </select>
      </label>
      <label>
        <span>Order</span>
        <select value={filters.sort} onChange={set("sort")}>
          <option value="priority">Most urgent first</option>
          <option value="newest">Newest first</option>
        </select>
      </label>
      <label className="check">
        <input type="checkbox" checked={filters.urgentOnly} onChange={set("urgentOnly")} />
        <span>Urgent only</span>
      </label>

      <p className="filter-count">
        {shown === total ? `${total} messages` : `${shown} of ${total} messages`}
        {shown !== total && (
          <button type="button" className="text-button" onClick={onReset}>Clear filters</button>
        )}
      </p>
    </div>
  );
}
