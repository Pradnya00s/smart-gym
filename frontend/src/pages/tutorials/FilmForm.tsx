export default function FilmForm() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">How to film your form for Smart Gym</h1>
      <p className="text-slate-300 leading-7 mt-4">
        To help Smart Gym analyze your posture accurately, follow these tips:
      </p>

      <ul className="list-disc list-inside text-slate-400 mt-4 space-y-2">
        <li>Place the camera at hip-to-chest height.</li>
        <li>Use good lighting — avoid strong backlight.</li>
        <li>Keep your full body visible during the movement.</li>
        <li>Use landscape orientation for best tracking.</li>
      </ul>
    </div>
  );
}
