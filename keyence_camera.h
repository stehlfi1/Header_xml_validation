#include <kr2_program_api/api_v1/bundles/custom_device.h>

#include <thread>
#include <atomic>
#include <vector>

#define SOCKET_TIMEOUT 1

// COMMANDS

namespace kswx_keyence_devices {

    class KeyenceCamera : public kr2_bundle_api::CustomDevice {
    public:

        KeyenceCamera(boost::shared_ptr<kr2_program_api::ProgramInterface> api,
                           const boost::property_tree::ptree &xml_bundle_node);
        
        virtual ~KeyenceCamera();
        
        //
        //
        // Mandatory event methods
        //
        //
        
        //! Called by the CBun Sandbox process on instantiation (master).
        virtual int onCreate();
        //! Called by the CBun Sandbox process on erase (master).
        virtual int onDestroy();
        
        //! Called by the User Spawner process on instantiation (slave).
        virtual int onBind();
        //! Called by the User Spawner process on instantiation (slave).
        virtual int onUnbind();

        void onHWReady(const kr2_signal::HWReady&);

        //
        //
        // Published custom methods, accessible from the CBun interface
        //
        //

        //! Fetch the results of the findObjects() method.
        
        virtual CBUN_PCALL triggerImage();
        virtual CBUN_PCALL triggerImageObj(kr2_program_api::Number &object_found);
        
        //! Fetch the recent object coordinates.
        virtual CBUN_PCALL getObjectPose(kr2_program_api::RobotPose &object_pose, int pose_type);
    protected:
        
        // fixed custom device methods
        
        virtual CBUN_PCALL onActivate(const boost::property_tree::ptree &param_tree);
        virtual CBUN_PCALL onDeactivate();
        
        virtual CBUN_PCALL onMount(const boost::property_tree::ptree &param_tree);
        virtual CBUN_PCALL onUnmount();

    //
    private:
        
        //int socket_fd_;
        struct Internals;
        boost::shared_ptr<Internals> internals_;

        // Standard socket allocation and configuration.
        int connectKeyence();
        // Wrap and send the Keyence command
        void sendCommand(const std::string &command);
        // Send byte to the camera
        void sendByte(int8_t byte);


        // Receive and response data
        bool recvResponse(std::string &response);

        bool processActivationParams(const boost::property_tree::ptree &tree);
    };
}
