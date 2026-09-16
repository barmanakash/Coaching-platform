import DashboardLayout from './DashboardLayout';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/admin' },
  { label: 'Approvals', path: '/admin/approvals' },
  { label: 'Students', path: '/admin/students' },
  { label: 'Teachers', path: '/admin/teachers' },
  { label: 'Courses', path: '/admin/courses' },
];

export default function AdminLayout() {
  return <DashboardLayout title="Admin Panel" navItems={NAV_ITEMS} />;
}
