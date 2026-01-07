import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

export const ImagePenIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M14.2639 15.9376L12.5958 14.2835C11.7909 13.4852 11.3884 13.0861 10.9266 12.9402C10.5204 12.8119 10.0838 12.8166 9.68048 12.9537C9.22188 13.1096 8.82814 13.5173 8.04068 14.3327L4.04409 18.2802M14.2639 15.9376L14.6053 15.5991C15.4112 14.7999 15.8141 14.4003 16.2765 14.2544C16.6831 14.1262 17.12 14.1312 17.5236 14.2688C17.9824 14.4252 18.3761 14.834 19.1634 15.6515L20 16.4936M14.2639 15.9376L18.275 19.9566M18.275 19.9566C17.9176 20.0001 17.4543 20.0001 16.8 20.0001H7.2C6.07989 20.0001 5.51984 20.0001 5.09202 19.7821C4.71569 19.5904 4.40973 19.2844 4.21799 18.9081C4.12796 18.7314 4.07512 18.5322 4.04409 18.2802M18.275 19.9566C18.5293 19.9257 18.7301 19.8728 18.908 19.7821C19.2843 19.5904 19.5903 19.2844 19.782 18.9081C20 18.4803 20 17.9202 20 16.8001V16.4936M12.5 4L7.2 4.00011C6.07989 4.00011 5.51984 4.00011 5.09202 4.21809C4.71569 4.40984 4.40973 4.7158 4.21799 5.09213C4 5.51995 4 6.08 4 7.20011V16.8001C4 17.4576 4 17.9222 4.04409 18.2802M20 11.5V16.4936M14 10.0002L16.0249 9.59516C16.2015 9.55984 16.2898 9.54219 16.3721 9.5099C16.4452 9.48124 16.5146 9.44407 16.579 9.39917C16.6515 9.34859 16.7152 9.28492 16.8425 9.1576L21 5.00015C21.5522 4.44787 21.5522 3.55244 21 3.00015C20.4477 2.44787 19.5522 2.44787 19 3.00015L14.8425 7.1576C14.7152 7.28492 14.6515 7.34859 14.6009 7.42112C14.556 7.4855 14.5189 7.55494 14.4902 7.62801C14.4579 7.71033 14.4403 7.79862 14.4049 7.97518L14 10.0002Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const SearchIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M15.7955 15.8111L21 21M18 10.5C18 14.6421 14.6421 18 10.5 18C6.35786 18 3 14.6421 3 10.5C3 6.35786 6.35786 3 10.5 3C14.6421 3 18 6.35786 18 10.5Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const ImagePlusIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M13 4H8.8C7.11984 4 6.27976 4 5.63803 4.32698C5.07354 4.6146 4.6146 5.07354 4.32698 5.63803C4 6.27976 4 7.11984 4 8.8V15.2C4 16.8802 4 17.7202 4.32698 18.362C4.6146 18.9265 5.07354 19.3854 5.63803 19.673C6.27976 20 7.11984 20 8.8 20H15.2C16.8802 20 17.7202 20 18.362 19.673C18.9265 19.3854 19.3854 18.9265 19.673 18.362C20 17.7202 20 16.8802 20 15.2V11M16 2V8M19 5H13M4.26185 17.7916L8.59883 13.4547C9.1962 12.8573 9.49488 12.5586 9.84067 12.4489C10.1428 12.3527 10.4689 12.3527 10.7711 12.4489C11.1169 12.5586 11.4155 12.8573 12.0129 13.4547L16.3499 17.7916M16.3499 17.7916L17.5822 16.5593C18.1796 15.9619 18.4783 15.6632 18.8241 15.5535C19.1262 15.4573 19.4523 15.4573 19.7544 15.5535C20.1002 15.6632 20.3989 15.9619 20.9963 16.5593L21 16.5629M16.3499 17.7916L16.5629 18.0046"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const BulbIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M9 21H15M12 3C8.68629 3 6 5.68629 6 9C6 10.2145 6.36084 11.3447 6.98117 12.2893C7.93507 13.7418 8.41161 14.4676 8.48704 14.6431C8.90918 15.5733 8.77556 16.4881 8.49543 17.0914C8.41135 17.2725 8.13316 17.8094 7.5766 18.8832C7.23255 19.5787 7.06053 19.9264 7.11972 20.2241C7.17103 20.4825 7.31809 20.7119 7.5328 20.8668C7.7814 21.0464 8.15596 21.0464 8.90508 21.0464H15.0949C15.844 21.0464 16.2186 21.0464 16.4672 20.8668C16.6819 20.7119 16.829 20.4825 16.8803 20.2241C16.9395 19.9264 16.7674 19.5787 16.4234 18.8832C15.8668 17.8094 15.5886 17.2725 15.5046 17.0914C15.2244 16.4881 15.0908 15.5733 15.513 14.6431C15.5884 14.4676 16.0649 13.7418 17.0188 12.2893C17.6392 11.3447 18 10.2145 18 9C18 5.68629 15.3137 3 12 3Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const ArrowDownIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M17 9.5C17 9.5 13.5811 13.5 12 13.5C10.4188 13.5 7 9.5 7 9.5M12 2.5V13M21 20.5C21 18.8431 16.9706 17.5 12 17.5C7.02944 17.5 3 18.8431 3 20.5"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const SunIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M12 3V4M12 20V21M4 12H3M6.31412 6.31412L5.5 5.5M17.6859 6.31412L18.5 5.5M6.31412 17.69L5.5 18.5001M17.6859 17.69L18.5 18.5001M21 12H20M16 12C16 14.2091 14.2091 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const MoonIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M13 6V3M18.5 12V7M14.5 4.5H11.5M21 9.5H16M15.5548 16.8151C16.7829 16.8151 17.9493 16.5506 19 16.0754C17.6867 18.9794 14.7642 21 11.3698 21C6.74731 21 3 17.2527 3 12.6302C3 9.23576 5.02061 6.31331 7.92462 5C7.44944 6.05072 7.18492 7.21708 7.18492 8.44523C7.18492 13.0678 10.9322 16.8151 15.5548 16.8151Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const FileLockIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M12 3H7.2C6.0799 3 5.51984 3 5.09202 3.21799C4.71569 3.40973 4.40973 3.71569 4.21799 4.09202C4 4.51984 4 5.0799 4 6.2V17.8C4 18.9201 4 19.4802 4.21799 19.908C4.40973 20.2843 4.71569 20.5903 5.09202 20.782C5.51984 21 6.0799 21 7.2 21H9M12 3L18 9M12 3V7.4C12 7.96005 12 8.24008 12.109 8.45399C12.2049 8.64215 12.3578 8.79513 12.546 8.89101C12.7599 9 13.0399 9 13.6 9H18M18 9V10M8 17H10M8 13H11M8 9H9M19 18.0039V17C19 15.8954 18.1046 15 17 15C15.8954 15 15 15.8954 15 17V18.0039M15.5 21H18.5C18.9659 21 19.1989 21 19.3827 20.9239C19.6277 20.8224 19.8224 20.6277 19.9239 20.3827C20 20.1989 20 19.9659 20 19.5C20 19.0341 20 18.8011 19.9239 18.6173C19.8224 18.3723 19.6277 18.1776 19.3827 18.0761C19.1989 18 18.9659 18 18.5 18H15.5C15.0341 18 14.8011 18 14.6173 18.0761C14.3723 18.1776 14.1776 18.3723 14.0761 18.6173C14 18.8011 14 19.0341 14 19.5C14 19.9659 14 20.1989 14.0761 20.3827C14.1776 20.6277 14.3723 20.8224 14.6173 20.9239C14.8011 21 15.0341 21 15.5 21Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const SearchCheckIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M15.7955 15.8111L21 21M18 10.5C18 14.6421 14.6421 18 10.5 18C6.35786 18 3 14.6421 3 10.5C3 6.35786 6.35786 3 10.5 3C14.6421 3 18 6.35786 18 10.5Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const CheckIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M4 12.6111L8.92308 17.5L20 6.5"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const XMarkIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M6 6L18 18M18 6L6 18"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const LockIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M12 14.5V16.5M7 10.0288C7.47142 10 8.05259 10 8.8 10H15.2C15.9474 10 16.5286 10 17 10.0288M7 10.0288C6.41168 10.0647 5.99429 10.1455 5.63803 10.327C5.07354 10.6146 4.6146 11.0735 4.32698 11.638C4 12.2798 4 13.1198 4 14.8V16.2C4 17.8802 4 18.7202 4.32698 19.362C4.6146 19.9265 5.07354 20.3854 5.63803 20.673C6.27976 21 7.11984 21 8.8 21H15.2C16.8802 21 17.7202 21 18.362 20.673C18.9265 20.3854 19.3854 19.9265 19.673 19.362C20 18.7202 20 17.8802 20 16.2V14.8C20 13.1198 20 12.2798 19.673 11.638C19.3854 11.0735 18.9265 10.6146 18.362 10.327C18.0057 10.1455 17.5883 10.0647 17 10.0288M7 10.0288V8C7 5.23858 9.23858 3 12 3C14.7614 3 17 5.23858 17 8V10.0288"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const AttentionIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path fillRule="evenodd" clipRule="evenodd" d="M12.8984 3.61441C12.5328 2.86669 11.4672 2.86669 11.1016 3.61441L3.30562 19.5608C2.98083 20.2251 3.46451 21 4.204 21H19.796C20.5355 21 21.0192 20.2251 20.6944 19.5608L12.8984 3.61441ZM9.30485 2.73599C10.4015 0.492834 13.5985 0.492825 14.6952 2.73599L22.4912 18.6824C23.4655 20.6754 22.0145 23 19.796 23H4.204C1.98555 23 0.534479 20.6754 1.50885 18.6824L9.30485 2.73599Z"
      fill="currentColor"
    />
    <path d="M11 8.49999C11 7.94771 11.4477 7.49999 12 7.49999C12.5523 7.49999 13 7.94771 13 8.49999V14C13 14.5523 12.5523 15 12 15C11.4477 15 11 14.5523 11 14V8.49999Z"
      fill="currentColor"
    />
    <path d="M13.5 18C13.5 18.8284 12.8285 19.5 12 19.5C11.1716 19.5 10.5 18.8284 10.5 18C10.5 17.1716 11.1716 16.5 12 16.5C12.8285 16.5 13.5 17.1716 13.5 18Z"
      fill="currentColor"
    />
  </svg>
);

export const HourglassIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M15 18H9M14 6H10M20 3H19M19 3H5M19 3C19 5.51022 17.7877 7.86592 15.7451 9.32495L12 12M5 3H4M5 3C5 5.51022 6.21228 7.86592 8.25493 9.32495L12 12M20 21H19M19 21H5M19 21C19 18.4898 17.7877 16.1341 15.7451 14.675L12 12M5 21H4M5 21C5 18.4898 6.21228 16.1341 8.25493 14.675L12 12"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const ChartIcon: React.FC<IconProps> = ({ className, size = 20 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path d="M8 9V11M12 7V11M16 8V11M3 3H5M21 3H19M12 18L7 21M12 18L17 21M12 18V21M12 18V15M19 3V11.8C19 12.9201 19 13.4802 18.782 13.908C18.5903 14.2843 18.2843 14.5903 17.908 14.782C17.4802 15 16.9201 15 15.8 15H12M19 3H5M5 3V11.8C5 12.9201 5 13.4802 5.21799 13.908C5.40973 14.2843 5.71569 14.5903 6.09202 14.782C6.51984 15 7.0799 15 8.2 15H12"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

