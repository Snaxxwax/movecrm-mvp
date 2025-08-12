import { Building2 } from 'lucide-react'

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary">
        <div className="flex flex-col justify-center items-center w-full px-12 text-white">
          <div className="text-center">
            <Building2 className="h-16 w-16 mx-auto mb-6" />
            <h1 className="text-4xl font-bold mb-4">MoveCRM</h1>
            <p className="text-xl mb-8 text-primary-foreground/80">
              Streamline your moving business with intelligent quote management
            </p>
            <div className="space-y-4 text-left max-w-md">
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-white rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-primary-foreground/90">
                  AI-powered item detection from photos
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-white rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-primary-foreground/90">
                  Automated pricing calculations
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-white rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-primary-foreground/90">
                  Multi-tenant customer management
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-white rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-primary-foreground/90">
                  Embeddable quote widgets
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Auth form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <Building2 className="h-12 w-12 mx-auto text-primary mb-4" />
            <h1 className="text-2xl font-bold text-gray-900">MoveCRM</h1>
          </div>
          
          {children}
        </div>
      </div>
    </div>
  )
}

