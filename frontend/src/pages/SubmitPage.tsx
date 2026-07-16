import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { submitReport } from "../lib/api";
import type { RenalHepaticFunction } from "../lib/types";

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function SubmitPage() {
  const navigate = useNavigate();
  const [prescriptionText, setPrescriptionText] = useState("");
  const [age, setAge] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [sex, setSex] = useState("");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState("");
  const [renalFunction, setRenalFunction] = useState<RenalHepaticFunction>("normal");
  const [hepaticFunction, setHepaticFunction] = useState<RenalHepaticFunction>("normal");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitReport({
        raw_prescription_text: prescriptionText,
        patient_profile: {
          age: age ? Number(age) : null,
          weight_kg: weightKg ? Number(weightKg) : null,
          sex: sex || null,
          allergies: splitList(allergies),
          conditions: splitList(conditions),
          renal_function: renalFunction,
          hepatic_function: hepaticFunction,
        },
      });
      navigate(`/processing/${response.report_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit prescription");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-1 text-2xl font-semibold">Medication Safety Check</h1>
      <p className="mb-6 text-sm text-gray-500">
        Submit a patient's current medication list and profile for a drug-interaction, allergy, and
        dosage safety review.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="prescription" className="mb-1 block text-sm font-medium">
            Prescription list
          </label>
          <textarea
            id="prescription"
            required
            rows={5}
            className="w-full rounded-md border border-gray-300 p-3 text-sm dark:border-gray-700 dark:bg-gray-900"
            placeholder="e.g. Warfarin 5mg daily, Aspirin 81mg daily"
            value={prescriptionText}
            onChange={(e) => setPrescriptionText(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="age" className="mb-1 block text-sm font-medium">
              Age
            </label>
            <input
              id="age"
              type="number"
              min={0}
              className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="weight" className="mb-1 block text-sm font-medium">
              Weight (kg)
            </label>
            <input
              id="weight"
              type="number"
              min={0}
              className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label htmlFor="sex" className="mb-1 block text-sm font-medium">
            Sex
          </label>
          <input
            id="sex"
            className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
            value={sex}
            onChange={(e) => setSex(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="allergies" className="mb-1 block text-sm font-medium">
            Known allergies (comma-separated)
          </label>
          <input
            id="allergies"
            className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
            placeholder="e.g. penicillin, sulfa"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="conditions" className="mb-1 block text-sm font-medium">
            Known conditions (comma-separated)
          </label>
          <input
            id="conditions"
            className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
            placeholder="e.g. chronic kidney disease"
            value={conditions}
            onChange={(e) => setConditions(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="renal" className="mb-1 block text-sm font-medium">
              Renal function
            </label>
            <select
              id="renal"
              className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={renalFunction}
              onChange={(e) => setRenalFunction(e.target.value as RenalHepaticFunction)}
            >
              <option value="normal">Normal</option>
              <option value="mild">Mild impairment</option>
              <option value="moderate">Moderate impairment</option>
              <option value="severe">Severe impairment</option>
            </select>
          </div>
          <div>
            <label htmlFor="hepatic" className="mb-1 block text-sm font-medium">
              Hepatic function
            </label>
            <select
              id="hepatic"
              className="w-full rounded-md border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={hepaticFunction}
              onChange={(e) => setHepaticFunction(e.target.value as RenalHepaticFunction)}
            >
              <option value="normal">Normal</option>
              <option value="mild">Mild impairment</option>
              <option value="moderate">Moderate impairment</option>
              <option value="severe">Severe impairment</option>
            </select>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Run safety check"}
        </button>
      </form>
    </div>
  );
}
