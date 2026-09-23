import DashboardLayout from './DashboardLayout';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/admin' },
  { label: 'Approvals', path: '/admin/approvals' },
  { label: 'Invitations', path: '/admin/invitations' },
  { label: 'Students', path: '/admin/students' },
  { label: 'Teachers', path: '/admin/teachers' },
  { label: 'Courses', path: '/admin/courses' },
  { label: 'Settings', path: '/admin/settings' },
  { label: 'Audit Log', path: '/admin/audit-log' },
];

export default function AdminLayout() {
  return <DashboardLayout title="Admin Panel" navItems={NAV_ITEMS} />;
}
