import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home-container">
      <h1>Disaster Relief Network</h1>

      <h3 className="status">🟢 Connected to Help Point</h3>

      <p className="description">
        Select the type of assistance or information you need.
      </p>

      <p className="network-status">
        Mesh Network Status: <strong>Online</strong>
      </p>

      <div className="button-group">
        <Link to="/medical">
          <button className="menu-button">Medical Assistance</button>
        </Link>

        <Link to="/food">
          <button className="menu-button">Food & Water</button>
        </Link>

        <Link to="/shelter">
          <button className="menu-button">Shelter</button>
        </Link>

        <Link to="/hazard">
          <button className="menu-button">Report Hazard</button>
        </Link>

        <Link to="/messages">
          <button className="menu-button">Messages</button>
        </Link>
      </div>
    </div>
  );
}

export default Home;