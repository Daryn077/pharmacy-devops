// Все запросы идут через Gateway: префиксы /api/pharmacy и /api/delivery он удаляет.
const PHARMACY = '/api/pharmacy'
const DELIVERY = '/api/delivery'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const text = await res.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!res.ok) {
    let detail = data && data.detail ? data.detail : `HTTP ${res.status}`
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join('; ')
    throw new Error(`${res.status}: ${detail}`)
  }
  return data
}

export const api = {
  medicines: (inStock) =>
    request(`${PHARMACY}/medicines${inStock ? '?in_stock=true' : ''}`),
  addMedicine: (body) =>
    request(`${PHARMACY}/medicines`, { method: 'POST', body: JSON.stringify(body) }),
  changeStock: (id, delta) =>
    request(`${PHARMACY}/medicines/${id}/stock`, { method: 'PATCH', body: JSON.stringify({ delta }) }),
  createOrder: (items, hasPrescription) =>
    request(`${PHARMACY}/orders`, {
      method: 'POST',
      body: JSON.stringify({ items, has_prescription: hasPrescription }),
    }),
  getOrder: (id) => request(`${PHARMACY}/orders/${id}`),
  districts: () => request(`${DELIVERY}/delivery/districts`),
  estimate: (district) =>
    request(`${DELIVERY}/delivery/estimate?district=${encodeURIComponent(district)}`),
}
