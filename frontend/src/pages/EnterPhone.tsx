import { useState } from 'react';
import { sendCode } from '../api/api';

function EnterPhone({ onPhoneSubmitted }: { onPhoneSubmitted: (phone: string) => void }) {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await sendCode(phone);
      if (res.status === 'code_sent') {
        onPhoneSubmitted(phone); 
      }
    } catch (err) {
      setError('Помилка надсилання коду. Перевірте номер.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Введіть номер телефону</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="tel"
          placeholder="+7XXXXXXXXXX"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Надсилаємо...' : 'Надіслати код'}
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

export default EnterPhone;
