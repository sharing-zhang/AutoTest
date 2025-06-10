export type RoleType = '' | '*' | 'admin' | 'user';
//状态管理库，定义多种属性，每一种属性都代表用户的一个状态
//以维护和更新应用程序中用户相关的数据，例如用户的登录状态、用户的个人信息、用户的权限等级等。
export interface UserState {
  user_id: any;
  user_name: any;
  user_token: any;

  admin_user_id: any;
  admin_user_name: any;
  admin_user_token: any;
}
