import DashboardLayout from './DashboardLayout';

const NAV_ITEMS = [
  { label: 'Institutes', path: '/super-admin' },
];

export default function SuperAdminLayout() {
  return <DashboardLayout title="Platform Admin" navItems={NAV_ITEMS} />;
}
