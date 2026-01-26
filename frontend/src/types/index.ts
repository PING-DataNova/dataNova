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
  id: string;
  name: string;
  role: 'juridique' | 'decisive';
  avatar?: string;
}