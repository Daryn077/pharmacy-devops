import { useEffect, useMemo, useState } from 'react'
import { api } from './api.js'

const money = (v) => `${Number(v).toLocaleString('ru-RU')} ₸`

function dayWord(n) {
  return `${n} күн`
}

export default function App() {
  const [medicines, setMedicines] = useState([])
  const [inStockOnly, setInStockOnly] = useState(false)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [cart, setCart] = useState({}) // { medicineId: qty }
  const [hasPrescription, setHasPrescription] = useState(false)
  const [order, setOrder] = useState(null)
  const [orderIdQuery, setOrderIdQuery] = useState('')
  const [form, setForm] = useState({ name: '', price: '', quantity: '', prescription: false })
  const [districts, setDistricts] = useState([])
  const [district, setDistrict] = useState('')
  const [estimate, setEstimate] = useState(null)

  const notify = (type, text) => {
    setToast({ type, text })
    clearTimeout(window.__toastTimer)
    window.__toastTimer = setTimeout(() => setToast(null), 4500)
  }

  const load = async () => {
    setLoading(true)
    try {
      setMedicines(await api.medicines(inStockOnly))
    } catch (e) {
      notify('error', `Дәрілер жүктелмеді — ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [inStockOnly])

  useEffect(() => {
    api.districts()
      .then((list) => { setDistricts(list); if (list.length) setDistrict(list[0].district) })
      .catch((e) => notify('error', `Аудандар жүктелмеді — ${e.message}`))
  }, [])

  const byId = useMemo(() => Object.fromEntries(medicines.map((m) => [m.id, m])), [medicines])
  const cartLines = Object.entries(cart)
    .filter(([, qty]) => qty > 0)
    .map(([id, qty]) => ({ medicine: byId[id], id: Number(id), qty }))
    .filter((l) => l.medicine)
  const cartPreview = cartLines.reduce((s, l) => s + l.medicine.price * l.qty, 0)
  const needsPrescription = cartLines.some((l) => l.medicine.prescription)

  const stats = {
    total: medicines.length,
    available: medicines.filter((m) => m.in_stock).length,
    rx: medicines.filter((m) => m.prescription).length,
  }

  const changeStock = async (id, delta) => {
    try {
      const updated = await api.changeStock(id, delta)
      setMedicines((list) => list.map((m) => (m.id === id ? updated : m)))
      notify('ok', `«${updated.name}» қалдығы: ${updated.quantity}`)
    } catch (e) {
      notify('error', e.message)
    }
  }

  const addToCart = (id) => setCart((c) => ({ ...c, [id]: (c[id] || 0) + 1 }))
  const setCartQty = (id, qty) => setCart((c) => ({ ...c, [id]: Math.max(0, qty) }))

  const submitOrder = async () => {
    if (!cartLines.length) return notify('error', 'Себет бос')
    try {
      const created = await api.createOrder(
        cartLines.map((l) => ({ medicine_id: l.id, qty: l.qty })),
        hasPrescription,
      )
      setOrder(created)
      setCart({})
      notify('ok', `#${created.id} тапсырыс рәсімделді. Сомасы: ${money(created.total)}`)
      load()
    } catch (e) {
      notify('error', e.message)
    }
  }

  const findOrder = async (e) => {
    e.preventDefault()
    if (!orderIdQuery) return
    try {
      setOrder(await api.getOrder(orderIdQuery))
    } catch (err) {
      notify('error', err.message)
    }
  }

  const addMedicine = async (e) => {
    e.preventDefault()
    try {
      const created = await api.addMedicine({
        name: form.name,
        price: Number(form.price),
        quantity: Number(form.quantity),
        prescription: form.prescription,
      })
      setForm({ name: '', price: '', quantity: '', prescription: false })
      notify('ok', `«${created.name}» қосылды (ID ${created.id})`)
      load()
    } catch (err) {
      notify('error', err.message)
    }
  }

  const calcDelivery = async (e) => {
    e.preventDefault()
    try {
      setEstimate(await api.estimate(district))
    } catch (err) {
      setEstimate(null)
      notify('error', err.message)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div className="brand">
          <div className="logo">✚</div>
          <div>
            <h1>Дәріхана</h1>
            <p>5-нұсқа · Қарағанды · Kubernetes микросервистері</p>
          </div>
        </div>
        <div className="stats">
          <div><b>{stats.total}</b><span>дәрі</span></div>
          <div><b>{stats.available}</b><span>қолда бар</span></div>
          <div><b>{stats.rx}</b><span>рецептпен</span></div>
        </div>
      </header>

      {toast && <div className={`toast ${toast.type}`}>{toast.text}</div>}

      <main className="layout">
        <section className="panel catalog">
          <div className="panel-head">
            <h2>Дәрілер тізімі</h2>
            <div className="head-actions">
              <label className="switch">
                <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} />
                <span>Тек қолда барлары</span>
              </label>
              <button className="ghost" onClick={load}>↻ Жаңарту</button>
            </div>
          </div>

          {loading ? (
            <p className="muted">Жүктелуде…</p>
          ) : medicines.length === 0 ? (
            <p className="muted">Дәрілер жоқ</p>
          ) : (
            <div className="grid">
              {medicines.map((m) => (
                <article key={m.id} className={`card ${m.in_stock ? '' : 'out'}`}>
                  <div className="card-top">
                    <span className="id">#{m.id}</span>
                    {m.prescription
                      ? <span className="badge rx">Рецептпен</span>
                      : <span className="badge otc">Рецептсіз</span>}
                  </div>
                  <h3>{m.name}</h3>
                  <div className="price">{money(m.price)}</div>
                  <div className={`stock ${m.in_stock ? '' : 'none'}`}>
                    {m.in_stock ? `Қалдық: ${m.quantity} дана` : 'Қолда жоқ'}
                  </div>
                  <div className="card-actions">
                    <div className="stepper" title="Қалдықты өзгерту">
                      <button onClick={() => changeStock(m.id, -1)}>−</button>
                      <span>қалдық</span>
                      <button onClick={() => changeStock(m.id, 1)}>+</button>
                    </div>
                    <button className="primary" disabled={!m.in_stock} onClick={() => addToCart(m.id)}>
                      Себетке
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}

          <form className="add-form" onSubmit={addMedicine}>
            <h3>Жаңа дәрі қосу</h3>
            <div className="row">
              <input required placeholder="Атауы" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input required type="number" min="1" step="any" placeholder="Бағасы, ₸" value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })} />
              <input required type="number" min="0" placeholder="Саны" value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
            </div>
            <div className="row">
              <label className="check">
                <input type="checkbox" checked={form.prescription}
                  onChange={(e) => setForm({ ...form, prescription: e.target.checked })} />
                Рецепт қажет
              </label>
              <button className="primary" type="submit">Қосу</button>
            </div>
          </form>
        </section>

        <aside className="side">
          <section className="panel">
            <h2>🛒 Себет</h2>
            {cartLines.length === 0 ? (
              <p className="muted">Себет бос. Дәріні «Себетке» батырмасымен қосыңыз.</p>
            ) : (
              <ul className="cart">
                {cartLines.map((l) => (
                  <li key={l.id}>
                    <div>
                      <b>{l.medicine.name}</b>
                      <small>{money(l.medicine.price)} × {l.qty}</small>
                    </div>
                    <input type="number" min="0" value={l.qty}
                      onChange={(e) => setCartQty(l.id, Number(e.target.value))} />
                  </li>
                ))}
              </ul>
            )}
            <label className="check">
              <input type="checkbox" checked={hasPrescription} onChange={(e) => setHasPrescription(e.target.checked)} />
              Рецептім бар
            </label>
            {needsPrescription && !hasPrescription && (
              <p className="warn">Себетте рецептпен берілетін дәрі бар</p>
            )}
            <div className="sum"><span>Алдын ала сома</span><b>{money(cartPreview)}</b></div>
            <button className="primary wide" onClick={submitOrder}>Тапсырыс беру</button>

            <form className="find" onSubmit={findOrder}>
              <input type="number" min="1" placeholder="Тапсырыс ID" value={orderIdQuery}
                onChange={(e) => setOrderIdQuery(e.target.value)} />
              <button className="ghost" type="submit">Табу</button>
            </form>

            {order && (
              <div className="receipt">
                <div className="receipt-head">Тапсырыс #{order.id}</div>
                {order.items.map((i) => (
                  <div key={i.medicine_id} className="receipt-row">
                    <span>{i.name} × {i.qty}</span><span>{money(i.subtotal)}</span>
                  </div>
                ))}
                <div className="receipt-total"><span>Жалпы сома</span><b>{money(order.total)}</b></div>
              </div>
            )}
          </section>

          <section className="panel delivery">
            <h2>🚚 Жеткізу мерзімі</h2>
            <form onSubmit={calcDelivery}>
              <select value={district} onChange={(e) => setDistrict(e.target.value)}>
                {districts.map((d) => <option key={d.district}>{d.district}</option>)}
              </select>
              <button className="primary wide" type="submit">Есептеу</button>
            </form>
            {estimate && (
              <div className="estimate">
                <span>{estimate.district}</span>
                <b>{dayWord(estimate.days)}</b>
              </div>
            )}
            <p className="muted small">Мерзімдер оқу жобасы үшін шартты түрде берілген.</p>
          </section>
        </aside>
      </main>

      <footer>Дәріхана · FastAPI + React + Nginx Gateway · namespace v5-pharmacy</footer>
    </div>
  )
}
