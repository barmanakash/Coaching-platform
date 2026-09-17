import { Routes, Route, Navigate } from 'react-router-dom';

import Login from '../pages/auth/Login';
import Signup from '../pages/auth/Signup';
import ProtectedRoute from './ProtectedRoute';

import AdminLayout from '../layouts/AdminLayout';
import TeacherLayout from '../layouts/TeacherLayout';
import StudentLayout from '../layouts/StudentLayout';

import AdminDashboard from '../pages/admin/AdminDashboard';
import StudentsPage from '../pages/admin/StudentsPage';
import TeachersPage from '../pages/admin/TeachersPage';
import CoursesPage from '../pages/admin/CoursesPage';
import ApprovalsPage from '../pages/admin/ApprovalsPage';

import TeacherDashboard from '../pages/teacher/TeacherDashboard';
import TeacherMyCourses from '../pages/teacher/TeacherMyCourses';
import TeacherCourseDetail from '../pages/teacher/TeacherCourseDetail';
import TeacherDoubts from '../pages/teacher/TeacherDoubts';
import TeacherChat from '../pages/teacher/TeacherChat';

import StudentDashboard from '../pages/student/StudentDashboard';
import StudentMyCourses from '../pages/student/StudentMyCourses';
import StudentCourseDetail from '../pages/student/StudentCourseDetail';
import StudentDoubts from '../pages/student/StudentDoubts';
import StudentChat from '../pages/student/StudentChat';

import ProfilePage from '../pages/ProfilePage';
import NotificationsPage from '../pages/NotificationsPage';
import ComingSoon from '../components/ComingSoon';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="students" element={<StudentsPage />} />
        <Route path="teachers" element={<TeachersPage />} />
        <Route path="courses" element={<CoursesPage />} />
      </Route>

      <Route
        path="/teacher"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TeacherDashboard />} />
        <Route path="courses" element={<TeacherMyCourses />} />
        <Route path="courses/:courseId" element={<TeacherCourseDetail />} />
        <Route path="students" element={<ComingSoon title="My Students" note="You'll see students enrolled in your courses here once enrollment is built." />} />
        <Route path="resources" element={<ComingSoon title="Resources" note="Upload notes, videos, and assignments for your courses here." />} />
        <Route path="classes" element={<ComingSoon title="Classes" note="Schedule and manage live classes here." />} />
        <Route path="doubts" element={<TeacherDoubts />} />
        <Route path="chat" element={<TeacherChat />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      <Route
        path="/student"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboard />} />
        <Route path="courses" element={<StudentMyCourses />} />
        <Route path="courses/:courseId" element={<StudentCourseDetail />} />
        <Route path="classes" element={<ComingSoon title="Upcoming Classes" note="Live classes you can join will appear here." />} />
        <Route path="resources" element={<ComingSoon title="Resources" note="Course materials will appear here." />} />
        <Route path="doubts" element={<StudentDoubts />} />
        <Route path="chat" element={<StudentChat />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
