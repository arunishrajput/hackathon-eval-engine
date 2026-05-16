'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApi } from '@/lib/api';

type Role = 'participant' | 'admin';

interface FormState {
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  role: Role;
}

interface FieldErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  full_name?: string;
  form?: string;
}

function FieldError({ message }: { message: string }) {
  return <p className="mt-1 text-xs text-red-400">{message}</p>;
}

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    role: 'participant',
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  const set = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = (): boolean => {
    const next: FieldErrors = {};
    if (!form.full_name.trim()) next.full_name = 'Full name is required';
    if (!form.email) next.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) next.email = 'Enter a valid email';
    if (!form.password) next.password = 'Password is required';
    else if (form.password.length < 8) next.password = 'Password must be at least 8 characters';
    if (!form.confirmPassword) next.confirmPassword = 'Please confirm your password';
    else if (form.password !== form.confirmPassword) next.confirmPassword = 'Passwords do not match';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setErrors({});
    setLoading(true);
    try {
      await authApi.register(form.email, form.password, form.full_name);
      router.replace('/auth/login');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setErrors({ form: axiosErr?.response?.data?.detail ?? 'Registration failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#13141a] px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-600 mb-4">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3M13.5 19.5H5.25A2.25 2.25 0 013 17.25V6.75A2.25 2.25 0 015.25 4.5h8.25" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">Create account</h1>
          <p className="mt-1 text-[#7e8088] text-sm">Join the hackathon platform</p>
        </div>

        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-2xl p-8">
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {errors.form && (
              <div className="bg-red-900/30 border border-red-800/50 text-red-400 px-4 py-3 rounded-lg text-sm">
                {errors.form}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                autoComplete="name"
                value={form.full_name}
                onChange={set('full_name')}
                placeholder="Alex Johnson"
                className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition ${
                  errors.full_name ? 'border-red-700' : 'border-[#3a3b48] focus:border-brand-600'
                }`}
              />
              {errors.full_name && <FieldError message={errors.full_name} />}
            </div>

            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
                Email
              </label>
              <input
                type="email"
                autoComplete="email"
                required
                value={form.email}
                onChange={set('email')}
                placeholder="you@example.com"
                className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition ${
                  errors.email ? 'border-red-700' : 'border-[#3a3b48] focus:border-brand-600'
                }`}
              />
              {errors.email && <FieldError message={errors.email} />}
            </div>

            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
                Password
              </label>
              <input
                type="password"
                autoComplete="new-password"
                required
                value={form.password}
                onChange={set('password')}
                placeholder="Min. 8 characters"
                className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition ${
                  errors.password ? 'border-red-700' : 'border-[#3a3b48] focus:border-brand-600'
                }`}
              />
              {errors.password && <FieldError message={errors.password} />}
            </div>

            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                autoComplete="new-password"
                value={form.confirmPassword}
                onChange={set('confirmPassword')}
                placeholder="Re-enter your password"
                className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition ${
                  errors.confirmPassword ? 'border-red-700' : 'border-[#3a3b48] focus:border-brand-600'
                }`}
              />
              {errors.confirmPassword && <FieldError message={errors.confirmPassword} />}
            </div>

            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
                Role
              </label>
              <select
                value={form.role}
                onChange={set('role')}
                className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-brand-600 transition"
              >
                <option value="participant">Participant</option>
                <option value="admin">Admin / Organizer</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-semibold transition-colors mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account...
                </span>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[#7e8088]">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
