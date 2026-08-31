import "./Form.css";
import { Link } from "react-router-dom";
import { useState } from "react";

function Shelter() {

    const [people, setPeople] = useState("");
    const [children, setChildren] = useState("No");
    const [pets, setPets] = useState("No");
    const [accessibility, setAccessibility] = useState("No");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit() {

        if (Number(people) <= 0) {
            alert("Please enter the number of people.");
            return;
        }

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            people,
            children,
            pets,
            accessibility,
            location,
            description
        };

        console.log("Shelter Request:", request);

        alert("Shelter request submitted successfully!");

        setPeople("");
        setChildren("No");
        setPets("No");
        setAccessibility("No");
        setLocation("");
        setDescription("");
    }

    return (
        <div className="page-container">

            <header className="page-header">
                <h1 className="page-title">Shelter Request</h1>

                <p className="page-description">
                    Request temporary shelter and provide information that
                    responders may need to find appropriate accommodations.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">
                    <label htmlFor="people">
                        Number of People
                    </label>

                    <input
                        id="people"
                        type="number"
                        min="1"
                        value={people}
                        onChange={(event) => setPeople(event.target.value)}
                        placeholder="Number of people"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="children">
                        Children Present?
                    </label>

                    <select
                        id="children"
                        value={children}
                        onChange={(event) => setChildren(event.target.value)}
                    >
                        <option>Yes</option>
                        <option>No</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="pets">
                        Pets Present?
                    </label>

                    <select
                        id="pets"
                        value={pets}
                        onChange={(event) => setPets(event.target.value)}
                    >
                        <option>Yes</option>
                        <option>No</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="accessibility">
                        Accessibility Needs
                    </label>

                    <select
                        id="accessibility"
                        value={accessibility}
                        onChange={(event) => setAccessibility(event.target.value)}
                    >
                        <option>No</option>
                        <option>Wheelchair</option>
                        <option>Medical Equipment</option>
                        <option>Other</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="location">
                        Approximate Location
                    </label>

                    <input
                        id="location"
                        type="text"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        placeholder="Example: Community Center entrance"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="description">
                        Additional Information
                    </label>

                    <textarea
                        id="description"
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        placeholder="Describe any special shelter requirements..."
                    />
                </div>

                <div className="form-actions">

                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={people === "" || location.trim() === ""}
                    >
                        Submit Shelter Request
                    </button>

                    <Link to="/" style={{ flex: 1 }}>
                        <button className="back-button">
                            Back to Home
                        </button>
                    </Link>

                </div>

            </div>
        </div>
    );
}

export default Shelter;