import { useEffect, useMemo, useState } from 'react'
import {
  ArrowDownLeft,
  ArrowUpLeft,
  BarChart3,
  Bell,
  Boxes,
  ChevronLeft,
  CircleDollarSign,
  ClipboardList,
  Clock3,
  Download,
  LayoutDashboard,
  LogOut,
  Menu,
  MoreHorizontal,
  PackagePlus,
  Plus,
  ReceiptText,
  Search,
  ShieldCheck,
  ShoppingBag,
  ShoppingCart,
  Smartphone,
  Sparkles,
  TrendingUp,
  UserCog,
  UserPlus,
  Users,
  Wifi,
  WifiOff,
  Wrench,
  X,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from 'recharts'
import { LoginScreen } from './auth'
import { roleLabels, useAuth } from './useAuth'
import { useStoreData } from './useStoreData'

const money = (value) => `${new Intl.NumberFormat('fa-IR').format(value)} تومان`
const number = (value) => new Intl.NumberFormat('fa-IR').format(value)

const initialProducts = [
  { id: 1, name: 'آیفون ۱۵ پرو مکس', sku: 'APL-15PM-256', category: 'گوشی موبایل', stock: 4, min: 3, buy: 78500000, price: 83400000 },
  { id: 2, name: 'سامسونگ Galaxy S24 Ultra', sku: 'SAM-S24U-256', category: 'گوشی موبایل', stock: 7, min: 3, buy: 61200000, price: 65900000 },
  { id: 3, name: 'شیائومی Redmi Note 13 Pro', sku: 'XMI-RN13P-256', category: 'گوشی موبایل', stock: 12, min: 4, buy: 16400000, price: 17950000 },
  { id: 4, name: 'ایرپاد پرو نسل ۲', sku: 'APL-APP2-USBC', category: 'لوازم جانبی', stock: 2, min: 5, buy: 11200000, price: 12900000 },
  { id: 5, name: 'شارژر ۲۵ وات سامسونگ', sku: 'SAM-CH25W', category: 'لوازم جانبی', stock: 3, min: 8, buy: 980000, price: 1250000 },
  { id: 6, name: 'گلس آیفون ۱۵', sku: 'ACC-GL-IPH15', category: 'محافظ صفحه', stock: 24, min: 10, buy: 120000, price: 290000 },
]

const initialSales = [
  { id: 'CT-1048', customer: 'مهدی اکبری', item: 'سامسونگ Galaxy S24 Ultra', total: 65900000, method: 'کارتخوان', time: 'امروز، ۱۱:۴۵', status: 'تکمیل' },
  { id: 'CT-1047', customer: 'سارا محمودی', item: 'ایرپاد پرو نسل ۲', total: 12900000, method: 'انتقال بانکی', time: 'امروز، ۱۰:۲۰', status: 'تکمیل' },
  { id: 'CT-1046', customer: 'علی مرادی', item: 'شارژر ۲۵ وات سامسونگ × ۲', total: 2500000, method: 'نقدی', time: 'دیروز، ۱۹:۱۰', status: 'تکمیل' },
  { id: 'CT-1045', customer: 'نگار احمدی', item: 'شیائومی Redmi Note 13 Pro', total: 17950000, method: 'کارتخوان', time: 'دیروز، ۱۷:۳۵', status: 'تکمیل' },
  { id: 'CT-1044', customer: 'رضا کریمی', item: 'گلس آیفون ۱۵ × ۳', total: 870000, method: 'نقدی', time: 'دیروز، ۱۴:۰۵', status: 'مرجوعی' },
]

const initialCustomers = [
  { id: 1, name: 'مهدی اکبری', phone: '۰۹۱۲ ۴۴۱ ۸۷۶۳', purchases: 5, spent: 142500000, last: 'امروز' },
  { id: 2, name: 'سارا محمودی', phone: '۰۹۳۵ ۲۳۱ ۹۸۱۰', purchases: 3, spent: 38200000, last: 'امروز' },
  { id: 3, name: 'علی مرادی', phone: '۰۹۱۹ ۷۸۰ ۱۲۴۴', purchases: 8, spent: 21800000, last: 'دیروز' },
  { id: 4, name: 'نگار احمدی', phone: '۰۹۰۲ ۱۵۴ ۴۳۱۱', purchases: 2, spent: 33650000, last: 'دیروز' },
  { id: 5, name: 'رضا کریمی', phone: '۰۹۱۰ ۸۸۲ ۳۱۰۷', purchases: 4, spent: 8700000, last: '۲ روز پیش' },
]

const initialRepairs = [
  { id: 'R-۲۴۸', customer: 'امیرحسین رضایی', device: 'iPhone 13', issue: 'تعویض باتری', status: 'در حال تعمیر', due: 'امروز، ۱۸:۰۰', price: 2800000 },
  { id: 'R-۲۴۷', customer: 'فاطمه زمانی', device: 'Galaxy A54', issue: 'تعویض ال‌سی‌دی', status: 'آماده تحویل', due: 'امروز، ۱۶:۰۰', price: 4200000 },
  { id: 'R-۲۴۶', customer: 'سامان نادری', device: 'Redmi Note 11', issue: 'مشکل شارژ', status: 'منتظر قطعه', due: 'فردا', price: 1100000 },
  { id: 'R-۲۴۵', customer: 'آرزو شریفی', device: 'iPhone 11', issue: 'تعویض اسپیکر', status: 'پذیرش شده', due: '۲ روز دیگر', price: 1900000 },
]

const chartData = [
  { day: 'شنبه', sales: 18.5 },
  { day: 'یکشنبه', sales: 26.2 },
  { day: 'دوشنبه', sales: 22.8 },
  { day: 'سه‌شنبه', sales: 35.4 },
  { day: 'چهارشنبه', sales: 31.6 },
  { day: 'پنجشنبه', sales: 48.7 },
  { day: 'جمعه', sales: 42.3 },
]

const navItems = [
  { id: 'dashboard', label: 'داشبورد', icon: LayoutDashboard },
  { id: 'sales', label: 'فروش و فاکتورها', icon: ReceiptText },
  { id: 'inventory', label: 'کالا و انبار', icon: Boxes },
  { id: 'customers', label: 'مشتریان', icon: Users },
  { id: 'repairs', label: 'تعمیرات', icon: Wrench, badge: 4 },
  { id: 'reports', label: 'گزارش‌ها', icon: BarChart3 },
  { id: 'personnel', label: 'پرسنل و دسترسی‌ها', icon: UserCog },
]

const rolePermissions = {
  admin: navItems.map((item) => item.id),
  sales: ['dashboard', 'sales', 'inventory', 'customers', 'repairs'],
  technician: ['dashboard', 'customers', 'repairs'],
}

function Logo() {
  return (
    <div className="logo">
      <div className="logo-mark"><Smartphone size={22} strokeWidth={2.5} /></div>
      <div><strong>سی‌تی‌تل</strong><span>مدیریت هوشمند فروشگاه</span></div>
    </div>
  )
}

function Modal({ title, subtitle, onClose, children }) {
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button modal-close" onClick={onClose}><X size={20} /></button>
        <div className="modal-heading"><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
        {children}
      </div>
    </div>
  )
}

function EmptyState({ icon: Icon = ClipboardList, title, text }) {
  return <div className="empty"><Icon size={36} /><h3>{title}</h3><p>{text}</p></div>
}

function StatCard({ title, value, change, note, icon: Icon, tone = 'teal', down = false }) {
  return (
    <article className="stat-card">
      <div className={`stat-icon ${tone}`}><Icon size={22} /></div>
      <div className="stat-title">{title}</div>
      <strong className="stat-value">{value}</strong>
      <div className="stat-meta">
        <span className={down ? 'trend down' : 'trend'}>{down ? <ArrowDownLeft size={14} /> : <ArrowUpLeft size={14} />}{change}</span>
        <span>{note}</span>
      </div>
    </article>
  )
}

function Dashboard({ products, sales, repairs, setPage, openSale, openProduct }) {
  const lowStock = products.filter((item) => item.stock <= item.min)
  return (
    <>
      <section className="welcome">
        <div><span className="eyebrow"><Sparkles size={15} /> خلاصه امروز</span><h1>سلام، روز پرفروشی داشته باشید 👋</h1><p>وضعیت فروشگاه سی‌تی‌تل در یک نگاه</p></div>
        <button className="primary-button" onClick={openSale}><Plus size={19} /> ثبت فروش جدید</button>
      </section>
      <section className="stats-grid">
        <StatCard title="فروش امروز" value={money(48350000)} change="۱۲٫۵٪" note="نسبت به دیروز" icon={CircleDollarSign} />
        <StatCard title="فاکتورهای امروز" value="۱۷ فاکتور" change="۳ فاکتور" note="بیشتر از دیروز" icon={ReceiptText} tone="blue" />
        <StatCard title="سود خالص امروز" value={money(7240000)} change="۸٫۲٪" note="حاشیه سود ۱۵٪" icon={TrendingUp} tone="violet" />
        <StatCard title="کالاهای کم‌موجود" value={`${number(lowStock.length)} کالا`} change="نیاز به اقدام" note="زیر نقطه سفارش" icon={Boxes} tone="amber" down />
      </section>
      <section className="dashboard-grid">
        <article className="panel chart-panel">
          <div className="panel-header">
            <div><h2>روند فروش هفتگی</h2><p>مبالغ به میلیون تومان</p></div>
            <select className="select-compact" aria-label="بازه گزارش"><option>۷ روز اخیر</option><option>۳۰ روز اخیر</option></select>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 4, left: 4, bottom: 0 }}>
                <defs><linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0f9d8b" stopOpacity={0.28} /><stop offset="100%" stopColor="#0f9d8b" stopOpacity={0} /></linearGradient></defs>
                <CartesianGrid strokeDasharray="4 6" vertical={false} stroke="#e8eeec" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#7b8b87', fontSize: 12 }} dy={10} />
                <Tooltip formatter={(value) => [`${number(value)} میلیون`, 'فروش']} contentStyle={{ border: '0', borderRadius: 14, boxShadow: '0 10px 30px rgba(20,50,45,.12)', direction: 'rtl' }} />
                <Area type="monotone" dataKey="sales" stroke="#0f8b7d" strokeWidth={3} fill="url(#salesGradient)" activeDot={{ r: 5, strokeWidth: 3, stroke: '#fff' }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel quick-panel">
          <div className="panel-header"><div><h2>دسترسی سریع</h2><p>کارهای پرتکرار فروشگاه</p></div></div>
          <div className="quick-grid">
            <button onClick={openSale}><span className="quick-icon teal"><ShoppingCart /></span><span>ثبت فروش</span></button>
            <button onClick={openProduct}><span className="quick-icon blue"><PackagePlus /></span><span>افزودن کالا</span></button>
            <button onClick={() => setPage('customers')}><span className="quick-icon violet"><UserPlus /></span><span>مشتری جدید</span></button>
            <button onClick={() => setPage('repairs')}><span className="quick-icon amber"><Wrench /></span><span>پذیرش تعمیر</span></button>
          </div>
        </article>
      </section>
      <section className="dashboard-grid lower-grid">
        <article className="panel">
          <div className="panel-header">
            <div><h2>آخرین فروش‌ها</h2><p>تراکنش‌های ثبت‌شده اخیر</p></div>
            <button className="text-button" onClick={() => setPage('sales')}>مشاهده همه <ChevronLeft size={16} /></button>
          </div>
          <SalesTable sales={sales.slice(0, 4)} compact />
        </article>
        <article className="panel stock-panel">
          <div className="panel-header">
            <div><h2>هشدار موجودی</h2><p>کالاهای نیازمند سفارش</p></div>
            <span className="count-badge">{number(lowStock.length)}</span>
          </div>
          <div className="stock-list">
            {lowStock.map((item) => (
              <div className="stock-row" key={item.id}>
                <div className="product-avatar"><ShoppingBag size={19} /></div>
                <div className="stock-info"><strong>{item.name}</strong><span>{item.sku}</span></div>
                <div className="stock-count"><strong>{number(item.stock)}</strong><span>عدد مانده</span></div>
              </div>
            ))}
          </div>
          <button className="secondary-button full" onClick={() => setPage('inventory')}>مدیریت موجودی</button>
        </article>
      </section>
      <section className="repair-strip">
        <div className="repair-art"><Wrench size={26} /></div>
        <div><strong>{number(repairs.filter((item) => item.status !== 'آماده تحویل').length)} دستگاه در جریان تعمیر</strong><span>یک دستگاه امروز آماده تحویل است</span></div>
        <button className="text-button light" onClick={() => setPage('repairs')}>مشاهده تعمیرات <ChevronLeft size={16} /></button>
      </section>
    </>
  )
}

function SalesTable({ sales, compact = false }) {
  if (!sales.length) return <EmptyState title="فروشی پیدا نشد" text="فروش جدید ثبت کنید یا عبارت جست‌وجو را تغییر دهید." />
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>شماره فاکتور</th><th>مشتری / کالا</th>{!compact && <th>روش پرداخت</th>}<th>مبلغ</th><th>زمان</th><th>وضعیت</th></tr></thead>
        <tbody>{sales.map((sale) => (
          <tr key={sale.id}>
            <td><strong className="invoice">{sale.id}</strong></td>
            <td><div className="table-person"><strong>{sale.customer}</strong><span>{sale.item}</span></div></td>
            {!compact && <td>{sale.method}</td>}
            <td><strong>{money(sale.total)}</strong></td>
            <td className="muted">{sale.time}</td>
            <td><span className={`status ${sale.status === 'مرجوعی' ? 'red' : 'green'}`}>{sale.status}</span></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function PageHeader({ eyebrow, title, description, button, onClick, icon: Icon = Plus }) {
  return (
    <div className="page-heading">
      <div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      {button && <button className="primary-button" onClick={onClick}><Icon size={18} />{button}</button>}
    </div>
  )
}

function SearchBar({ value, onChange, placeholder }) {
  return <label className="search-box"><Search size={18} /><input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>
}

function Inventory({ products, search, setSearch, openProduct }) {
  const filtered = products.filter((item) => `${item.name} ${item.sku} ${item.category}`.toLowerCase().includes(search.toLowerCase()))
  const totalValue = products.reduce((sum, item) => sum + item.buy * item.stock, 0)
  return (
    <>
      <PageHeader eyebrow="مدیریت انبار" title="کالاها و موجودی" description="موجودی، قیمت خرید و فروش کالاهای فروشگاه را کنترل کنید." button="افزودن کالای جدید" onClick={openProduct} icon={PackagePlus} />
      <section className="mini-stats">
        <div><span>تعداد کالاها</span><strong>{number(products.length)} مدل</strong></div>
        <div><span>ارزش موجودی</span><strong>{money(totalValue)}</strong></div>
        <div><span>کم‌موجود</span><strong className="warn-text">{number(products.filter((item) => item.stock <= item.min).length)} کالا</strong></div>
      </section>
      <section className="panel page-panel">
        <div className="toolbar"><SearchBar value={search} onChange={setSearch} placeholder="جست‌وجوی نام، کد یا دسته‌بندی..." /><select><option>همه دسته‌ها</option><option>گوشی موبایل</option><option>لوازم جانبی</option></select></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>کالا</th><th>کد کالا</th><th>دسته‌بندی</th><th>قیمت خرید</th><th>قیمت فروش</th><th>موجودی</th><th></th></tr></thead>
            <tbody>{filtered.map((item) => (
              <tr key={item.id}>
                <td><div className="product-cell"><div className="product-avatar"><Smartphone size={19} /></div><strong>{item.name}</strong></div></td>
                <td className="muted ltr">{item.sku}</td><td>{item.category}</td><td>{money(item.buy)}</td><td><strong>{money(item.price)}</strong></td>
                <td><span className={`stock-pill ${item.stock <= item.min ? 'low' : ''}`}>{number(item.stock)} عدد</span></td>
                <td><button className="icon-button"><MoreHorizontal size={19} /></button></td>
              </tr>
            ))}</tbody>
          </table>
          {!filtered.length && <EmptyState title="کالایی پیدا نشد" text="عبارت جست‌وجو را تغییر دهید." />}
        </div>
      </section>
    </>
  )
}

function Sales({ sales, search, setSearch, openSale }) {
  const filtered = sales.filter((item) => `${item.id} ${item.customer} ${item.item}`.toLowerCase().includes(search.toLowerCase()))
  const total = sales.filter((item) => item.status !== 'مرجوعی').reduce((sum, item) => sum + item.total, 0)
  return (
    <>
      <PageHeader eyebrow="صندوق فروشگاه" title="فروش و فاکتورها" description="تراکنش‌ها را ثبت کنید و سوابق فروش را ببینید." button="ثبت فروش جدید" onClick={openSale} />
      <section className="mini-stats"><div><span>مجموع فروش</span><strong>{money(total)}</strong></div><div><span>تعداد فاکتورها</span><strong>{number(sales.length)} فاکتور</strong></div><div><span>میانگین هر خرید</span><strong>{money(Math.round(total / Math.max(sales.length, 1)))}</strong></div></section>
      <section className="panel page-panel">
        <div className="toolbar"><SearchBar value={search} onChange={setSearch} placeholder="جست‌وجوی فاکتور، مشتری یا کالا..." /><button className="secondary-button"><Download size={17} /> خروجی اکسل</button></div>
        <SalesTable sales={filtered} />
      </section>
    </>
  )
}

function Customers({ customers, search, setSearch, openCustomer }) {
  const filtered = customers.filter((item) => `${item.name} ${item.phone}`.includes(search))
  return (
    <>
      <PageHeader eyebrow="باشگاه مشتریان" title="مشتریان" description="اطلاعات تماس و سابقه خرید مشتریان وفادار را مدیریت کنید." button="مشتری جدید" onClick={openCustomer} icon={UserPlus} />
      <section className="panel page-panel">
        <div className="toolbar"><SearchBar value={search} onChange={setSearch} placeholder="جست‌وجوی نام یا شماره تماس..." /><span className="result-count">{number(filtered.length)} مشتری</span></div>
        <div className="customer-grid">
          {filtered.map((customer) => (
            <article className="customer-card" key={customer.id}>
              <div className="customer-top"><div className="customer-avatar">{customer.name.charAt(0)}</div><button className="icon-button"><MoreHorizontal /></button></div>
              <h3>{customer.name}</h3><p className="ltr">{customer.phone}</p>
              <div className="customer-data"><div><span>تعداد خرید</span><strong>{number(customer.purchases)}</strong></div><div><span>ارزش خرید</span><strong>{money(customer.spent)}</strong></div></div>
              <div className="customer-footer"><span>آخرین خرید</span><strong>{customer.last}</strong></div>
            </article>
          ))}
        </div>
        {!filtered.length && <EmptyState icon={Users} title="مشتری پیدا نشد" text="مشتری جدیدی اضافه کنید یا جست‌وجو را تغییر دهید." />}
      </section>
    </>
  )
}

function Repairs({ repairs, openRepair, updateRepair }) {
  const statuses = ['پذیرش شده', 'در حال تعمیر', 'منتظر قطعه', 'آماده تحویل']
  return (
    <>
      <PageHeader eyebrow="خدمات پس از فروش" title="مدیریت تعمیرات" description="از پذیرش تا تحویل، وضعیت دستگاه مشتری را پیگیری کنید." button="پذیرش دستگاه" onClick={openRepair} icon={Wrench} />
      <section className="repair-board">
        {statuses.map((status) => (
          <div className="repair-column" key={status}>
            <div className="column-heading"><span className={`status-dot s-${statuses.indexOf(status)}`} /> <strong>{status}</strong><span>{number(repairs.filter((item) => item.status === status).length)}</span></div>
            {repairs.filter((item) => item.status === status).map((repair) => (
              <article className="repair-card" key={repair.id}>
                <div className="repair-card-top"><span>{repair.id}</span><Smartphone size={18} /></div>
                <h3>{repair.device}</h3><p>{repair.issue}</p>
                <div className="repair-customer"><Users size={15} />{repair.customer}</div>
                <div className="repair-time"><Clock3 size={15} />{repair.due}</div>
                <strong className="repair-price">{money(repair.price)}</strong>
                {status !== 'آماده تحویل' && <button className="advance-button" onClick={() => updateRepair(repair.id, statuses[statuses.indexOf(status) + 1])}>انتقال به مرحله بعد <ChevronLeft size={15} /></button>}
              </article>
            ))}
          </div>
        ))}
      </section>
    </>
  )
}

function Reports({ sales, products }) {
  const salesTotal = sales.filter((item) => item.status !== 'مرجوعی').reduce((sum, item) => sum + item.total, 0)
  const stockValue = products.reduce((sum, item) => sum + item.buy * item.stock, 0)
  return (
    <>
      <PageHeader eyebrow="تحلیل عملکرد" title="گزارش‌های فروشگاه" description="تصویر روشنی از فروش، سود و سرمایه موجود در انبار داشته باشید." button="دریافت گزارش" icon={Download} onClick={() => window.print()} />
      <section className="stats-grid reports-stats">
        <StatCard title="فروش ثبت‌شده" value={money(salesTotal)} change="۱۲٫۵٪" note="رشد در این دوره" icon={CircleDollarSign} />
        <StatCard title="سرمایه انبار" value={money(stockValue)} change={`${number(products.reduce((sum, item) => sum + item.stock, 0))} عدد`} note="کالای موجود" icon={Boxes} tone="blue" />
        <StatCard title="سود تخمینی" value={money(Math.round(salesTotal * 0.15))} change="۱۵٪" note="حاشیه سود" icon={TrendingUp} tone="violet" />
      </section>
      <section className="panel report-chart">
        <div className="panel-header"><div><h2>عملکرد هفتگی فروش</h2><p>مقایسه مبلغ فروش روزانه به میلیون تومان</p></div></div>
        <div className="chart large"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData}><defs><linearGradient id="reportGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0f9d8b" stopOpacity={0.3} /><stop offset="100%" stopColor="#0f9d8b" stopOpacity={0} /></linearGradient></defs><CartesianGrid strokeDasharray="4 6" vertical={false} stroke="#e8eeec" /><XAxis dataKey="day" axisLine={false} tickLine={false} /><Tooltip /><Area type="monotone" dataKey="sales" stroke="#0f8b7d" strokeWidth={3} fill="url(#reportGradient)" /></AreaChart></ResponsiveContainer></div>
      </section>
    </>
  )
}

function SaleForm({ products, customers, onSubmit, onClose }) {
  const [productId, setProductId] = useState(products[0]?.id ?? '')
  const [customer, setCustomer] = useState(customers[0]?.name ?? 'مشتری حضوری')
  const [qty, setQty] = useState(1)
  const [method, setMethod] = useState('کارتخوان')
  const product = products.find((item) => item.id === Number(productId))
  const submit = (event) => {
    event.preventDefault()
    if (!product || qty < 1 || qty > product.stock) return
    onSubmit({ product, customer, qty, method })
  }
  return (
    <form onSubmit={submit} className="form">
      <label><span>انتخاب کالا</span><select value={productId} onChange={(event) => setProductId(event.target.value)}>{products.filter((item) => item.stock > 0).map((item) => <option key={item.id} value={item.id}>{item.name} — موجودی {number(item.stock)}</option>)}</select></label>
      <label><span>مشتری</span><select value={customer} onChange={(event) => setCustomer(event.target.value)}><option>مشتری حضوری</option>{customers.map((item) => <option key={item.id}>{item.name}</option>)}</select></label>
      <div className="form-row"><label><span>تعداد</span><input type="number" min="1" max={product?.stock || 1} value={qty} onChange={(event) => setQty(Number(event.target.value))} /></label><label><span>روش پرداخت</span><select value={method} onChange={(event) => setMethod(event.target.value)}><option>کارتخوان</option><option>نقدی</option><option>انتقال بانکی</option></select></label></div>
      <div className="invoice-summary"><span>مبلغ قابل پرداخت</span><strong>{money((product?.price || 0) * qty)}</strong></div>
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>انصراف</button><button className="primary-button">ثبت و صدور فاکتور</button></div>
    </form>
  )
}

function ProductForm({ onSubmit, onClose }) {
  const [form, setForm] = useState({ name: '', sku: '', category: 'گوشی موبایل', stock: 1, min: 3, buy: '', price: '' })
  const field = (key) => ({ value: form[key], onChange: (event) => setForm({ ...form, [key]: event.target.value }) })
  return (
    <form className="form" onSubmit={(event) => { event.preventDefault(); onSubmit(form) }}>
      <label><span>نام کالا</span><input required placeholder="مثلاً آیفون ۱۶ پرو" {...field('name')} /></label>
      <div className="form-row"><label><span>کد کالا</span><input required className="ltr" placeholder="SKU-001" {...field('sku')} /></label><label><span>دسته‌بندی</span><select {...field('category')}><option>گوشی موبایل</option><option>لوازم جانبی</option><option>محافظ صفحه</option><option>قطعات تعمیر</option></select></label></div>
      <div className="form-row thirds"><label><span>موجودی اولیه</span><input type="number" min="0" required {...field('stock')} /></label><label><span>نقطه سفارش</span><input type="number" min="0" required {...field('min')} /></label><label><span>قیمت خرید (تومان)</span><input type="number" min="0" required {...field('buy')} /></label></div>
      <label><span>قیمت فروش (تومان)</span><input type="number" min="0" required {...field('price')} /></label>
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>انصراف</button><button className="primary-button">افزودن به انبار</button></div>
    </form>
  )
}

function CustomerForm({ onSubmit, onClose }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  return (
    <form className="form" onSubmit={(event) => { event.preventDefault(); onSubmit({ name, phone }) }}>
      <label><span>نام و نام خانوادگی</span><input required value={name} onChange={(event) => setName(event.target.value)} placeholder="نام مشتری" /></label>
      <label><span>شماره موبایل</span><input required className="ltr" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="۰۹۱۲ ۱۲۳ ۴۵۶۷" /></label>
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>انصراف</button><button className="primary-button">ذخیره مشتری</button></div>
    </form>
  )
}

function RepairForm({ onSubmit, onClose }) {
  const [form, setForm] = useState({ customer: '', device: '', issue: '', price: '' })
  const field = (key) => ({ value: form[key], onChange: (event) => setForm({ ...form, [key]: event.target.value }) })
  return (
    <form className="form" onSubmit={(event) => { event.preventDefault(); onSubmit(form) }}>
      <div className="form-row"><label><span>نام مشتری</span><input required {...field('customer')} /></label><label><span>مدل دستگاه</span><input required placeholder="مثلاً iPhone 12" {...field('device')} /></label></div>
      <label><span>شرح خرابی</span><textarea required rows="3" placeholder="مشکل دستگاه را بنویسید..." {...field('issue')} /></label>
      <label><span>هزینه تخمینی (تومان)</span><input required type="number" min="0" {...field('price')} /></label>
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>انصراف</button><button className="primary-button">ثبت پذیرش</button></div>
    </form>
  )
}

function Personnel({ profile, online, installAvailable, installed, installApp }) {
  const roles = [
    { id: 'admin', title: 'مدیر فروشگاه', text: 'دسترسی کامل به فروش، انبار، گزارش‌ها و پرسنل', icon: ShieldCheck },
    { id: 'sales', title: 'فروشنده', text: 'ثبت فروش، مشتریان، مشاهده موجودی و تعمیرات', icon: ShoppingCart },
    { id: 'technician', title: 'تعمیرکار', text: 'پذیرش، پیگیری و تکمیل سفارش‌های تعمیر', icon: Wrench },
  ]
  return (
    <>
      <PageHeader eyebrow="مدیریت تیم" title="پرسنل و دسترسی‌ها" description="هر کاربر فقط بخش‌های مرتبط با نقش خود را مشاهده می‌کند." />
      <section className={`connection-panel ${online ? 'online' : ''}`}>
        <div className="connection-icon">{online ? <Wifi size={22} /> : <WifiOff size={22} />}</div>
        <div><strong>{online ? 'دیتابیس مرکزی فعال است' : 'حالت نمایشی محلی فعال است'}</strong><span>{online ? 'تغییرات این دستگاه با گوشی همه پرسنل همگام می‌شود.' : 'برای همگام‌سازی بین گوشی‌ها، متغیرهای Supabase را هنگام انتشار تنظیم کنید.'}</span></div>
        <span className="connection-state">{online ? 'آنلاین' : 'نیاز به تنظیم'}</span>
      </section>
      <section className="personnel-grid">
        <article className="panel current-user-card">
          <div className="panel-header"><div><h2>کاربر فعلی</h2><p>حساب فعال روی این دستگاه</p></div></div>
          <div className="current-user">
            <div className="large-avatar">{profile?.full_name?.charAt(0) || 'ک'}</div>
            <div><strong>{profile?.full_name}</strong><span>{roleLabels[profile?.role] || 'پرسنل فروشگاه'}</span></div>
            <span className="active-pill"><i /> فعال</span>
          </div>
        </article>
        <article className="panel install-card">
          <div className="install-copy"><div className="install-icon"><Smartphone size={25} /></div><div><h2>نصب روی گوشی</h2><p>برنامه را بدون نیاز به اپ‌استور روی صفحه اصلی نصب کنید.</p></div></div>
          {installed ? <span className="installed-badge">✓ برنامه نصب شده است</span> : installAvailable ? <button className="primary-button" onClick={installApp}><Download size={17} /> نصب برنامه</button> : <div className="install-help"><b>اندروید:</b> منوی مرورگر ← افزودن به صفحه اصلی<br /><b>آیفون:</b> Share ← Add to Home Screen</div>}
        </article>
      </section>
      <section className="panel roles-panel">
        <div className="panel-header"><div><h2>سطوح دسترسی</h2><p>نقش هر کاربر در Supabase قابل تنظیم است.</p></div></div>
        <div className="roles-grid">
          {roles.map(({ id, title, text, icon: Icon }) => <article key={id} className={profile?.role === id ? 'current-role' : ''}><div><Icon size={20} /></div><strong>{title}</strong><p>{text}</p>{profile?.role === id && <span>نقش فعلی شما</span>}</article>)}
        </div>
      </section>
    </>
  )
}

export default function App() {
  const auth = useAuth()
  const [page, setPage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(null)
  const [toast, setToast] = useState('')
  const [installPrompt, setInstallPrompt] = useState(null)
  const [installed, setInstalled] = useState(() => window.matchMedia('(display-mode: standalone)').matches)
  const [products, setProducts] = useStoreData('cttel-products', initialProducts, auth.user?.id, auth.online)
  const [sales, setSales] = useStoreData('cttel-sales', initialSales, auth.user?.id, auth.online)
  const [customers, setCustomers] = useStoreData('cttel-customers', initialCustomers, auth.user?.id, auth.online)
  const [repairs, setRepairs] = useStoreData('cttel-repairs', initialRepairs, auth.user?.id, auth.online)

  const currentNav = useMemo(() => navItems.find((item) => item.id === page), [page])
  const role = auth.profile?.role || 'sales'
  const allowedPages = rolePermissions[role] || rolePermissions.sales
  const visibleNav = navItems.filter((item) => allowedPages.includes(item.id))

  useEffect(() => {
    const captureInstall = (event) => {
      event.preventDefault()
      setInstallPrompt(event)
    }
    const markInstalled = () => {
      setInstalled(true)
      setInstallPrompt(null)
    }
    window.addEventListener('beforeinstallprompt', captureInstall)
    window.addEventListener('appinstalled', markInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', captureInstall)
      window.removeEventListener('appinstalled', markInstalled)
    }
  }, [])

  const notify = (message) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2800)
  }
  const navigate = (target) => {
    if (!allowedPages.includes(target)) {
      notify('حساب شما به این بخش دسترسی ندارد')
      return
    }
    setPage(target); setSearch(''); setSidebarOpen(false)
  }
  const guardedAction = (allowed, action) => {
    if (allowed) action()
    else notify('این عملیات برای نقش شما مجاز نیست')
  }
  const installApp = async () => {
    if (!installPrompt) return
    await installPrompt.prompt()
    const choice = await installPrompt.userChoice
    if (choice.outcome === 'accepted') setInstallPrompt(null)
  }
  const addProduct = (form) => {
    setProducts((current) => [...current, { ...form, id: Date.now(), stock: Number(form.stock), min: Number(form.min), buy: Number(form.buy), price: Number(form.price) }])
    setModal(null); notify('کالای جدید با موفقیت به انبار اضافه شد')
  }
  const addCustomer = ({ name, phone }) => {
    setCustomers((current) => [{ id: Date.now(), name, phone, purchases: 0, spent: 0, last: 'بدون خرید' }, ...current])
    setModal(null); notify('اطلاعات مشتری ذخیره شد')
  }
  const addSale = ({ product, customer, qty, method }) => {
    const total = product.price * qty
    setSales((current) => [{ id: `CT-${1049 + current.length - initialSales.length}`, customer, item: `${product.name}${qty > 1 ? ` × ${number(qty)}` : ''}`, total, method, time: 'همین حالا', status: 'تکمیل' }, ...current])
    setProducts((current) => current.map((item) => item.id === product.id ? { ...item, stock: item.stock - qty } : item))
    setCustomers((current) => current.map((item) => item.name === customer ? { ...item, purchases: item.purchases + 1, spent: item.spent + total, last: 'همین حالا' } : item))
    setModal(null); notify('فروش ثبت و موجودی انبار به‌روزرسانی شد')
  }
  const addRepair = (form) => {
    setRepairs((current) => [{ ...form, id: `R-${number(249 + current.length - initialRepairs.length)}`, price: Number(form.price), status: 'پذیرش شده', due: 'تعیین نشده' }, ...current])
    setModal(null); notify('پذیرش دستگاه با موفقیت ثبت شد')
  }
  const updateRepair = (id, status) => {
    setRepairs((current) => current.map((item) => item.id === id ? { ...item, status } : item))
    notify(`وضعیت تعمیر به «${status}» تغییر کرد`)
  }

  const canSell = ['admin', 'sales'].includes(role)
  const canManageInventory = role === 'admin'
  const canRepair = ['admin', 'technician'].includes(role)
  const canAddCustomer = ['admin', 'sales'].includes(role)
  const pageContent = {
    dashboard: <Dashboard products={products} sales={sales} repairs={repairs} setPage={navigate} openSale={() => guardedAction(canSell, () => setModal('sale'))} openProduct={() => guardedAction(canManageInventory, () => setModal('product'))} />,
    sales: <Sales sales={sales} search={search} setSearch={setSearch} openSale={() => guardedAction(canSell, () => setModal('sale'))} />,
    inventory: <Inventory products={products} search={search} setSearch={setSearch} openProduct={() => guardedAction(canManageInventory, () => setModal('product'))} />,
    customers: <Customers customers={customers} search={search} setSearch={setSearch} openCustomer={() => guardedAction(canAddCustomer, () => setModal('customer'))} />,
    repairs: <Repairs repairs={repairs} openRepair={() => guardedAction(canRepair, () => setModal('repair'))} updateRepair={(id, status) => guardedAction(canRepair, () => updateRepair(id, status))} />,
    reports: <Reports sales={sales} products={products} />,
    personnel: <Personnel profile={auth.profile} online={auth.online} installAvailable={Boolean(installPrompt)} installed={installed} installApp={installApp} />,
  }

  if (auth.loading) return <div className="app-loading"><div className="loading-logo"><Smartphone /></div><span>در حال آماده‌سازی سی‌تی‌تل...</span></div>
  if (!auth.user) return <LoginScreen signIn={auth.signIn} demoSignIn={auth.demoSignIn} online={auth.online} />

  return (
    <div className="app-shell">
      {sidebarOpen && <button className="sidebar-overlay" onClick={() => setSidebarOpen(false)} aria-label="بستن منو" />}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <Logo />
        <nav>
          <span className="nav-label">منوی اصلی</span>
          {visibleNav.map(({ id, label, icon: Icon, badge }) => <button key={id} className={page === id ? 'active' : ''} onClick={() => navigate(id)}><Icon size={20} /><span>{label}</span>{badge && <b>{number(badge)}</b>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <button onClick={auth.signOut}><LogOut size={19} /> خروج از حساب</button>
          <div className="support-card"><div><Smartphone size={18} /></div><strong>سی‌تی‌تل روی گوشی شما</strong><span>{installed ? 'برنامه روی این دستگاه نصب شده است' : 'برای دسترسی سریع برنامه را نصب کنید'}</span><button onClick={() => installPrompt ? installApp() : notify('از منوی مرورگر، افزودن به صفحه اصلی را انتخاب کنید')}>{installed ? 'نصب شده ✓' : 'نصب برنامه'}</button></div>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <div className="topbar-title"><button className="menu-button" onClick={() => setSidebarOpen(true)}><Menu /></button><div><span>صفحه / {currentNav?.label}</span><strong>{currentNav?.label}</strong></div></div>
          <div className="topbar-actions">
            <div className="global-search"><Search size={17} /><input placeholder="جست‌وجو در فروشگاه..." /></div>
            <span className={`sync-indicator ${auth.online ? 'online' : ''}`}>{auth.online ? <Wifi size={15} /> : <WifiOff size={15} />}{auth.online ? 'همگام' : 'محلی'}</span>
            <button className="notification"><Bell size={20} /><i /></button>
            <div className="profile"><div className="avatar">{auth.profile?.full_name?.charAt(0) || 'ک'}</div><div><strong>{auth.profile?.full_name}</strong><span>{roleLabels[role]}</span></div></div>
          </div>
        </header>
        <main>{pageContent[page]}</main>
      </div>
      {modal === 'sale' && <Modal title="ثبت فروش جدید" subtitle="کالا و اطلاعات پرداخت را وارد کنید." onClose={() => setModal(null)}><SaleForm products={products} customers={customers} onSubmit={addSale} onClose={() => setModal(null)} /></Modal>}
      {modal === 'product' && <Modal title="افزودن کالای جدید" subtitle="مشخصات و قیمت کالا را وارد کنید." onClose={() => setModal(null)}><ProductForm onSubmit={addProduct} onClose={() => setModal(null)} /></Modal>}
      {modal === 'customer' && <Modal title="افزودن مشتری" subtitle="اطلاعات تماس مشتری را ثبت کنید." onClose={() => setModal(null)}><CustomerForm onSubmit={addCustomer} onClose={() => setModal(null)} /></Modal>}
      {modal === 'repair' && <Modal title="پذیرش دستگاه" subtitle="مشخصات دستگاه و خرابی را ثبت کنید." onClose={() => setModal(null)}><RepairForm onSubmit={addRepair} onClose={() => setModal(null)} /></Modal>}
      {toast && <div className="toast"><span>✓</span>{toast}</div>}
    </div>
  )
}
