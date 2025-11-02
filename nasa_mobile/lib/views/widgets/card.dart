import 'package:flutter/material.dart';

class ActionCard extends StatefulWidget {
  const ActionCard({
    super.key,
    required this.icon,
    required this.title,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final VoidCallback? onTap;

  @override
  State<ActionCard> createState() => _ActionCardState();
}

class _ActionCardState extends State<ActionCard> {
  @override
  Widget build(BuildContext context) {
    final isEnabled = widget.onTap != null;
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4.0),
        child: Card(
          elevation: isEnabled ? 4 : 1,
          color: isEnabled ? Theme.of(context).cardColor : Colors.grey[800],
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(
              color: isEnabled
                  ? Theme.of(context).colorScheme.secondary
                  : Colors.grey[700]!,
              width: isEnabled ? 2 : 1,
            ),
          ),
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    widget.icon,
                    size: 36,
                    color: isEnabled
                        ? Theme.of(context).colorScheme.secondary
                        : Colors.grey[600],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.title,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: isEnabled
                          ? Theme.of(context).textTheme.bodyLarge!.color
                          : Theme.of(context).textTheme.bodyMedium!.color,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
