import { useEffect, useMemo, useState } from "react";
import { useGateway, isUrgent } from "./live.js";
import TopStrip from "./components/TopStrip.jsx";
import Filters from "./components/Filters.jsx";
import MessageLog from "./components/MessageLog.jsx";
import MessageDetail from "./components/MessageDetail.jsx";
import MeshHealth from "./components/MeshHealth.jsx";
import SecurityLog from "./components/SecurityLog.jsx";

const DEFAULT_FILTERS = { type: "all", hp: "all", ack: "open", urgentOnly: false, sort: "priority" };

function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(t);
  }, [intervalMs]);
  return now;
}

export default function App() {
  const gw = useGateway();
  const now = useNow();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState(null);

  const all = useMemo(() => Object.values(gw.messages), [gw.messages]);

  const visible = useMemo(() => {
    const rows = all.filter(
      (m) =>
        (filters.type === "all" || m.msg_type === filters.type) &&
        (filters.hp === "all" || String(m.hp_id) === filters.hp) &&
        (filters.ack === "all" ||
          (filters.ack === "open" ? m.ack_state !== "resolved" : m.ack_state === filters.ack)) &&
        (!filters.urgentOnly || isUrgent(m)),
    );
    const byTime = (a, b) => b.received_at - a.received_at;
    rows.sort(filters.sort === "newest" ? byTime : (a, b) => b.priority - a.priority || byTime(a, b));
    return rows;
  }, [all, filters]);

  const selected = selectedId != null ? gw.messages[selectedId] : null;

  // Esc closes the detail panel
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && setSelectedId(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="board">
      <TopStrip
        messages={all}
        events={gw.events}
        link={gw.link}
        health={gw.health}
        now={now}
        activeType={filters.type}
        onType={(type) => setFilters((f) => ({ ...f, type: f.type === type ? "all" : type }))}
      />

      <main className="log-column">
        <Filters
          filters={filters}
          setFilters={setFilters}
          meta={gw.meta}
          shown={visible.length}
          total={all.length}
          onReset={() => setFilters(DEFAULT_FILTERS)}
        />
        <MessageLog
          rows={visible}
          now={now}
          arrivals={gw.arrivals}
          selectedId={selectedId}
          onSelect={setSelectedId}
          loading={gw.link === "connecting"}
          anyMessages={all.length > 0}
        />
      </main>

      <aside className="side-column">
        {selected ? (
          <MessageDetail message={selected} now={now} onClose={() => setSelectedId(null)} onUpdated={gw.applyUpdate} />
        ) : (
          <>
            <MeshHealth nodes={Object.values(gw.nodes)} meta={gw.meta} now={now} />
            <SecurityLog events={gw.events} now={now} />
          </>
        )}
      </aside>

      <footer className="disclaimer">
        MeshAid is a research prototype. It does not guarantee delivery and is not a substitute for 911 or official dispatch.
      </footer>
    </div>
  );
}
