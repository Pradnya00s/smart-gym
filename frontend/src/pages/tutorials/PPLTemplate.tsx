export default function PPLTemplate() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Beginner push–pull–legs template</h1>

      <p className="text-slate-300 mt-4 leading-7">
        A simple PPL routine you can follow with AI workout planner assistance:
      </p>

      <h2 className="text-xl font-semibold mt-6">Push day</h2>
      <ul className="list-disc list-inside text-slate-400 mt-2 space-y-2">
        <li>Bench press</li>
        <li>Shoulder press</li>
        <li>Tricep dips</li>
      </ul>

      <h2 className="text-xl font-semibold mt-6">Pull day</h2>
      <ul className="list-disc list-inside text-slate-400 mt-2 space-y-2">
        <li>Lat pulldown</li>
        <li>Row variations</li>
        <li>Bicep curls</li>
      </ul>

      <h2 className="text-xl font-semibold mt-6">Legs day</h2>
      <ul className="list-disc list-inside text-slate-400 mt-2 space-y-2">
        <li>Squats or leg press</li>
        <li>Hamstring curls</li>
        <li>Calf raises</li>
      </ul>
    </div>
  );
}
