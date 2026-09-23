import { ago } from "../live.js";

const ROLE_ORDER = { gateway: 0, relay: 1, help_point: 2, node: 3 };
const ROLE_NAME = { gateway: "Gateway", relay: "Relay", help_point: "Help Point", node: "Node" };
const STATUS_NAME = { up: "Up", degraded: "Quiet", down: "Down" };

function liveStatus(n, meta, now) {
  // Recomputed every tick so a node that goes silent turns quiet/down without a server push.
  if (!meta || n.last_heard == null) return n.status;
  const age = now / 1000 - n.last_heard;
  if (age > meta.node_down_after) return "down";
  if (age > meta.node_degraded_after) return "degraded";
  return "up";
}

export default function MeshHealth({ nodes: raw, meta, now }) {
  const nodes = raw.map((n) => ({ ...n, status: liveStatus(n, meta, now) }));
  const sorted = [...nodes].sort(
    (a, b) => (ROLE_ORDER[a.role] ?? 9) - (ROLE_ORDER[b.role] ?? 9) || String(a.label).localeCompare(String(b.label)),
  );
  const down = nodes.filter((n) => n.status !== "up").length;

  return (
    <section className="panel" aria-labelledby="mesh-title">
      <h2 id="mesh-title">
        Mesh
        <span className="panel-note">
          {nodes.length === 0 ? "no nodes heard" : down ? `${down} of ${nodes.length} not reporting` : `all ${nodes.length} nodes up`}
        </span>
      </h2>
      {nodes.length === 0 ? (
        <p className="panel-empty">The gateway hasn't heard from any mesh nodes yet.</p>
      ) : (
        <ul className="nodes">
          {sorted.map((n) => (
            <li key={n.node_num} className={`node node-${n.status}`}>
              <span className="node-mark" aria-hidden="true" />
              <span className="node-name">
                {n.label}
                <span className="node-role">{ROLE_NAME[n.role] || n.role}</span>
              </span>
              <span className="node-status">{STATUS_NAME[n.status]}</span>
              <span className="node-seen">{ago(n.last_heard, now)}</span>
              <span className="node-radio">
                {n.hops_away != null && `${n.hops_away} hop${n.hops_away === 1 ? "" : "s"}`}
                {n.snr != null && ` / ${Number(n.snr).toFixed(1)} dB`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
