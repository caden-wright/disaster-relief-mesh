import "./Form.css";
import { Link } from "react-router-dom";
import { useState } from "react";
import SubmissionResult from "../components/SubmissionResult";
import { submitMessage } from "../api/helpPoint";

function Medical() {
    const [severity, setSeverity] = useState("Serious");
    const [condition, setCondition] = useState("Injury or bleeding");
    const [patientName, setPatientName] = useState("");
    const [patientAge, setPatientAge] = useState("");

    const [submissionStatus, setSubmissionStatus] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit() {
        if (
            patientAge !== "" &&
            (
                Number(patientAge) < 0 ||
                Number(patientAge) > 255
            )
        ) {
            alert("Please enter a valid patient age.");
            return;
        }

        const request = {
            type: "medical_urgent",
            severity,
            condition,
            patient_name: patientName.trim(),
            patient_age:
                patientAge === ""
                    ? 0
                    : Number(patientAge)
        };

        setSubmitting(true);

        try {
            const result = await submitMessage(request);

            setSubmissionStatus(result.status);
        } catch (error) {
            console.error("Medical Request failed:", error);

            setSubmissionStatus("error");
        } finally {
            setSubmitting(false);
        }
    }

    function resetForm() {
        setSubmissionStatus(null);
        setSeverity("Serious");
        setCondition("Injury or bleeding");
        setPatientName("");
        setPatientAge("");
    }

    if (submissionStatus) {
        return (
            <div className="page-container">

                <SubmissionResult
                    status={submissionStatus}
                    onReset={resetForm}
                />

            </div>
        );
    }

    return (
        <div className="page-container">

            <header className="page-header">
                <h1 className="page-title">
                    Medical Assistance
                </h1>

                <p className="page-description">
                    Report an urgent medical need to emergency coordinators.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">
                    <label htmlFor="severity">
                        Severity
                    </label>

                    <select
                        id="severity"
                        value={severity}
                        onChange={(event) =>
                            setSeverity(event.target.value)
                        }
                    >
                        <option>Minor</option>
                        <option>Serious</option>
                        <option>Critical</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="condition">
                        Medical Condition
                    </label>

                    <select
                        id="condition"
                        value={condition}
                        onChange={(event) =>
                            setCondition(event.target.value)
                        }
                    >
                        <option>Injury or bleeding</option>
                        <option>Breathing difficulty</option>
                        <option>Unconscious or unresponsive</option>
                        <option>Chest pain</option>
                        <option>Other or unknown</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="patient-name">
                        Patient Name
                        <span> (optional)</span>
                    </label>

                    <input
                        id="patient-name"
                        type="text"
                        maxLength="20"
                        value={patientName}
                        onChange={(event) =>
                            setPatientName(event.target.value)
                        }
                        placeholder="Name if known"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="patient-age">
                        Patient Age
                        <span> (optional)</span>
                    </label>

                    <input
                        id="patient-age"
                        type="number"
                        min="0"
                        max="255"
                        value={patientAge}
                        onChange={(event) =>
                            setPatientAge(event.target.value)
                        }
                        placeholder="Age if known"
                    />
                </div>

                <div className="form-actions">

                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={submitting}
                    >
                        {submitting
                            ? "Submitting..."
                            : "Submit Medical Request"}
                    </button>

                    <Link
                        to="/"
                        className="back-button"
                    >
                        Back to Home
                    </Link>

                </div>

            </div>
        </div>
    );
}

export default Medical;