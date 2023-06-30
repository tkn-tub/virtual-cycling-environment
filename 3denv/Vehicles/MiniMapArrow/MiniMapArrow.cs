using Godot;
using System.Diagnostics;
public class MiniMapArrow : Spatial
{
    // Declare member variables here. Examples:
    // private int a = 2;
    // private string b = "text";
    private bool _isPlayerArrow { get; set; } = false;
    private float _timer = 3.0f;
    private Stopwatch _transparencyTimer;
    private double _transparencyLevel = 1;
    private int _stepLengthMilliseconds = 200;
    private float _opacityReductionFactor = .79f;
    private MeshInstance _mesh;
    // Called when the node enters the scene tree for the first time.
    public override void _Ready()
    {
        _transparencyTimer = Stopwatch.StartNew();
        _mesh = GetNode<MeshInstance>("minimap_arrow");
    }
    //  // Called every frame. 'delta' is the elapsed time since the previous frame.
    public override void _Process(float delta)
    {

    }

    public override void _PhysicsProcess(float delta)
    {
        if (!_isPlayerArrow)
        {
            UpdateTransparency();
            _timer -= delta;
            if (_timer <= 0)
            {
                QueueFree();
            }
        }
    }
    public void SetIsPlayerArrow(bool isPlayerArrow)
    {
        _isPlayerArrow = isPlayerArrow;
    }
    public void ChangeColor(Color color)
    {
        var material = new SpatialMaterial();
        material.AlbedoColor = color;
        material.FlagsTransparent = true;
        GetNode<MeshInstance>("minimap_arrow").MaterialOverride = material;
    }

    private void UpdateTransparency()
    {
        if (_transparencyTimer.ElapsedMilliseconds > _stepLengthMilliseconds * _transparencyLevel)
        {
            _transparencyLevel++;
            var material = new SpatialMaterial();
            material.FlagsTransparent = true;
            SpatialMaterial _meshMaterial = (SpatialMaterial)_mesh.GetActiveMaterial(0);
            Color c = _meshMaterial.AlbedoColor;
            c.a *= _opacityReductionFactor;
            material.AlbedoColor = c;

            _mesh.MaterialOverride = material;
            _transparencyLevel++;

        }
    }
}
