export interface Regulation {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'validated' | 'rejected' | 'to-review';
  type: string;
  dateCreated: Date;
  reference?: string;
}

export interface User {
  id?: string;
  name?: string;
  email?: string;
  fullName?: string;
  role: 'juridique' | 'decisive' | 'admin' | string;
  avatar?: string;
}