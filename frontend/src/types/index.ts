export interface User {
  id: number;
  name: string;
  email?: string;
  telegram_id?: string;
  username?: string;
  avatar?: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Group {
  id: number;
  name: string;
  description?: string;
  invite_code: string;
  owner_id: number;
  min_people_for_meeting: number;
  created_at: string;
}

export interface Member {
  id: number;
  user_id: number;
  name: string;
  username?: string;
  telegram_id?: string;
  avatar?: string;
  role: "OWNER" | "ADMIN" | "MEMBER";
}

export interface Availability {
  id: number;
  user_id: number;
  group_id: number;
  date: string;
  status: "free" | "busy" | "maybe" | "unknown";
  start_time?: string;
  end_time?: string;
  recurring_rule?: string;
}

export interface Idea {
  id: number;
  group_id: number;
  title: string;
  description?: string;
  cost?: string;
  category?: string;
  photo_url?: string;
  links?: string;
  tags?: string;
  location?: string;
  suggestor_id: number;
  suggestor_name?: string;
  is_archived: boolean;
  reactions: Record<string, number>;
  created_at: string;
}

export interface Comment {
  id: number;
  idea_id: number;
  user_id: number;
  user_name?: string;
  text: string;
  created_at: string;
}

export interface Vote {
  id: number;
  group_id: number;
  title: string;
  vote_type: string;
  status: string;
  category?: string;
  options: VoteOption[];
  ends_at: string;
  created_at: string;
}

export interface VoteOption {
  id: number;
  idea_id: number;
  idea_title: string;
  votes_count: number;
}

export type RsvpStatus = "going" | "not_going" | "maybe";

export interface Participant {
  user_id: number;
  user_name: string;
  status: RsvpStatus;
}

export interface Meeting {
  id: number;
  group_id: number;
  idea_id?: number;
  idea_title?: string;
  title: string;
  description?: string;
  date: string;
  time?: string;
  location?: string;
  photo_url?: string;
  creator_id: number;
  creator_name?: string;
  participants: Participant[];
  created_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message?: string;
  data?: string;
  is_read: boolean;
  created_at: string;
}

export interface Recommendation {
  title: string;
  description?: string;
  category?: string;
  url?: string;
  image_url?: string;
  price?: string;
  date?: string;
  location?: string;
  source?: string;
}
