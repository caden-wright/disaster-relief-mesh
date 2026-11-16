import { useState } from "react";
import { Link } from "react-router-dom";
import "./Form.css";
import SubmissionResult from "../components/SubmissionResult";
import { submitMessage } from "../api/helpPoint";

// Codes match shared/codes.json -> checkin_status (DI-06).
const STATUS_OPTIONS = [
    { code: 1, label: "Safe", detail: "Everyone in the group is safe." },
    { code: 2, label: "Safe, needs assistance", detail: "Safe for now, but the group needs help." },
    { code: 3, label: "Not safe", detail: "The group is in danger or cannot stay here." }
];

function CheckIn() {
    const [status, setStatus] = useState(1);
    const [people, setPeople] = useState("1");
    const [submissionStatus, setSubmissionStatus] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit() {
        if (Number(people) <= 0) {
            alert("Please enter a valid number of people.");
            return;
        }

        const request = {
            type: "safety_checkin",
            status,
            people: Number(people)
        };

        setSubmitting(true);

        try {
            const result = await submitMessage(request);
            setSubmissionStatus(result.status);
        } catch (error) {
            console.error("Safety Check-In failed:", error);
            setSubmissionStatus("error");
        } finally {
            setSubmitting(false);
        }
    }

    if (submissionStatus) {
        return (
            <div className="page-container">
                <SubmissionResult
                    status={submissionStatus}
                    onReset={() => {
                        setSubmissionStatus(null);
                        setStatus(1);
                        setPeople("1");
                    }}
                />
            </div>
        );
    }

    return (
        <div className="page-container">
            <header className="page-header">
                <h1 className="page-title">Safety Check-In</h1>
                <p className="page-description">
                    Let emergency coordinators know how you and your
                    group are doing at this Help Point.
                </p>
            </header>

            <div className="form-card">
                <div className="form-group">
                    <label htmlFor="status">Status</label>
                    <select
                        id="status"
                        value={status}
                        onChange={(event) => setStatus(Number(event.target.value))}
                    >
                        {STATUS_OPTIONS.map((option) => (
                            <option key={option.code} value={option.code}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                    <p className="form-hint">
                        {STATUS_OPTIONS.find((option) => option.code === status)?.detail}
                    </p>
                </div>

                <div className="form-group">
                    <label htmlFor="people">Number of People</label>
                    <input
                        id="people"
                        type="number"
                        min="1"
                        value={people}
                        onChange={(event) => setPeople(event.target.value)}
                    />
                </div>

                <div className="form-actions">
                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={people === "" || submitting}
                    >
                        {submitting ? "Submitting..." : "Submit Safety Check-In"}
                    </button>

                    <Link to="/" className="back-button">
                        Back to Home
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default CheckIn;
