import logoImg from '../../assets/logo.png';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function Logo({ size = 'md', className = '' }: LogoProps) {
  const sizes = {
    sm: 'h-8',
    md: 'h-10',
    lg: 'h-14',
    xl: 'h-20',
  };

  return (
    <img 
      src={logoImg} 
      alt="AERO RECON-3D" 
      className={`w-auto object-contain ${sizes[size]} ${className}`} 
    />
  );
}
